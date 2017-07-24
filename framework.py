# 
#
# Based on: 
#   Framework for fuzzing things
#   author: Chris Bisnett

import sys
import os
import random
import subprocess
import time
import shutil
import shlex
import signal 
import sys
import socket

from ptrace.debugger.debugger import PtraceDebugger
from ptrace.debugger.child import createChild
from ptrace.debugger.process_event import ProcessExit
from ptrace.debugger.ptrace_signal import ProcessSignal
from signal import SIGCHLD, SIGTRAP, SIGSEGV
import logging

GLOBAL = {
    "process": 0,
    "prev_seed": 0,
}


# Global cache of inputs
_inputs = []

fuzzers = {
    "Dumb": 
    {
        "name": "Dumb",
        "file": "fuzzer_dumb.py",
        "args": '%(seed)s "%(input)s" %(output)s',
    },
    "Radamsa": 
    {
        "name": "Radamsa",
        "file": "radamsa/bin/radamsa",
        "args": '-s %(seed)s -o %(output)s "%(input)s"',
    },
}


def _setupEnvironment(config):
    """
    Performs one-time setup tasks before starting the fuzzer
    """
    # Silence warnings from the ptrace library
    logging.getLogger().setLevel(logging.ERROR)

    # AddressSanitizer will report memory leaks by default on exit. We don't
    # care about those since they aren't vulnerabilities, so disable it
    #os.environ["ASAN_OPTIONS"] = "detect_leaks=false:abort_on_error=true"

    # dont report leak on exits
    #os.environ["ASAN_OPTIONS"]="color=never:verbosity=0:leak_check_at_exit=false:abort_on_error=true:log_path=" + config["projdir"] + "asanlogs/"
    os.environ["ASAN_OPTIONS"]="color=never:verbosity=0:leak_check_at_exit=false:abort_on_error=true"

    # Tell Glibc to abort on heap corruption but not dump a bunch of output
    os.environ["MALLOC_CHECK_"] = "2"


def _chooseInput(config):
    """
    Chooses an input from the inputs directory specified in the configuration
    """
    global _inputs
    if len(_inputs) == 0:
        _inputs = os.listdir(config["inputs"])

    if len(_inputs) == 0:
        print "No input files"
        sys.exit(0)

    return os.path.join(config["inputs"], random.choice(_inputs))


def _generateSeed(config):
    """
    Generate a random seed to pass to the fuzzer
    """
    return random.randint(0, 2**64 - 1)


def _runFuzzer(config, inputFile, seed, outputFile, count):
    """
    Run the fuzzer specified in the configuration
    """
    fuzzerData = fuzzers[ config["fuzzer"] ]
    if not fuzzerData:
        print "Could not find fuzzer with name: " + config["fuzzer"]
        sys.exit(0)

    args = fuzzerData["args"] % ({
        "seed" : seed, 
        "input" : inputFile,
        "output" : outputFile, 
        "count" : count})
    subprocess.call(config["basedir"] + "/" + fuzzerData["file"] + " " + args, shell=True)


def _checkForCrash(config, event):
    """
    Check if the target application has crashed
    """
    # Normal exits have no signal associated with them
    if event.signum is not None or event.exitcode != 0:
        return event

    return None


def _handleOutcome(config, event, inputFile, seed, outputFile, count):
    """
    Save the output from the fuzzer for replay and make a note of the outcome
    """
    # Save a log
    with open(os.path.join(config["outcome_dir"], str(seed)+".txt"), "w") as f:
        f.write("Input: %s\n" % inputFile)
        f.write("Seed: %s\n" % seed)
        f.write("Count: %d\n" % count)
        f.write("Fuzzer: %s\n" % config["fuzzer"])
        f.write("Target: %s\n" % config["target_bin"])
        f.write("Target: %s\n" % time.strftime("%c"))


        if hasattr(event, "signum") and event.signum:
            f.write("Signal: %d\n" % event.signum)

        if hasattr(event, "exitcode") and event.exitcode:
            f.write("Exit code: %d\n" % event.exitcode)

    # Save the output
    try:
        shutil.copy(outputFile, os.path.join(config["outcome_dir"],
            os.path.basename(outputFile)))
    except Exception as e:
        print "Failed to copy output file:", outputFile


def printConfig(config):
    print "Config for thread:  " + config["threadId"]
    print "  Running fuzzer:   ", config["fuzzer"]
    print "  Outcomde dir:     ", config["outcome_dir"]
    print "  Target:           ", config["target_bin"]
    print "  Target port:      ", str(config["target_port"])
    print "  Input dir:        ", config["inputs"]
    print "  Analyze response: ", config["response_analysis"]
    

def _runTarget(config):
    #args = config["target_args"] % ({"input" : outputFile})
    #cmd = shlex.split(config["target_bin"])
    #pid = createChild(cmd, True, None)
    popenArg = [ config["target_bin"], str(config["target_port"]) ]
    DEVNULL = open(os.devnull, 'wb')

    #subprocess.call([config["basedir"] + "/" + fuzzerData["file"], args], shell=True, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
    #p = subprocess.Popen(popenArg, close_fds=True)
    p = subprocess.Popen(popenArg, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
    time.sleep(1)
    return p


def startServer(config):
    # Step 5: Run the target
    p = _runTarget(config)

    #######################################################################
    # This is where the magic happens. We monitor the process to determine
    # if it has crashed
    # Attach to the process with ptrace
    #print "Ptrace pid: " + str(p.pid)
    #dbg = PtraceDebugger()
    #proc = dbg.addProcess(p.pid, True)
    #proc.cont()
    GLOBAL["process"] = p


def stopServer():
    GLOBAL["process"].terminate()


def signal_handler(signal, frame):
    print "Terminating pid: " + str(GLOBAL["process"].pid)
    stopServer()
    sys.exit(0)


def isAlive():
    if GLOBAL["process"].poll() == None: 
        return True
    else:
        return False


def testServerConnection(config):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', config["target_port"])

    try: 
        sock.connect(server_address)
    except socket.error, exc:
        # server down
        return False
    
    sock.close()

    return True


def sendDataToServer(config, file):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', config["target_port"])

    try: 
        sock.connect(server_address)
    except socket.error, exc:
        # server down
        return False

    # sock.setblocking(0)
    file = open(file, "r")
    data = file.read()

    sock.sendall(data)

    if config["response_analysis"]:
        sock.settimeout(0.1)
        try: 
            r = sock.recv(1024)
            # print "Received len: " + str(len(r))
        except Exception,e:
            #print "Recv exception"
            pass

    file.close()
    sock.close()

    return True


def getServerCrashInfo(confg, file): 
    #p = _runTarget(config)

    while False:
        try:
            # Check if there is an event pending for the target applicaiton
            # This will return immediately with either an event or None if
            # there is no event. We do this so we can kill the target after
            # it reaches the timeout
            event = dbg.waitProcessEvent(blocking=False)

            # Check if the process exited
            if type(event) == ProcessExit:
                # Step 6: Check for crash
                outcome = checkForCrash(config, event)

                # The target application exited so we're done here
                break

            elif type(event) == ProcessSignal:
                # SIGCHLD simply notifies the parent that one of it's
                # children processes has exited or changed (exec another
                # process). It's not a bug so we tell the process to
                # continue and we loop again to get the next event
                if event.signum == SIGCHLD:
                    event.process.cont()
                    continue

                outcome = checkForCrash(config, event)
                break

        except KeyboardInterrupt:
            done = True
            break

        # Check if the process has reached the timeout
        if time.time() >= endTime:
            break
        else:
            # Give the CPU some timeslices to run other things
            time.sleep(0.1)


def handlePrevCrash(config, outExt, inFile, outcome, runFuzzer, handleOutcome):
    # regenerate old outFile
    outFilePrev = os.path.join(config["temp_dir"], str(GLOBAL["prev_seed"]) + outExt)
    runFuzzer(config, inFile, GLOBAL["prev_seed"], outFilePrev, GLOBAL["prev_count"])
    handleOutcome(config, outcome, inFile, GLOBAL["prev_seed"], outFilePrev, GLOBAL["prev_count"])
    sys.stdout.write("!")
    sys.stdout.flush()


# The main fuzzing loop
# all magic is performed here
def doFuzz(config, setupEnvironment=_setupEnvironment, chooseInput=_chooseInput,
    generateSeed=_generateSeed, runFuzzer=_runFuzzer, runTarget=_runTarget,
    checkForCrash=_checkForCrash, handleOutcome=_handleOutcome):
    seed = 0
    count = 0
    outcome = None
    crashCount = 0 # number of crashes, absolute
    crashCountNew = 0 # number of crashes since last minimizing
    threadId = 1
    gcovAnalysisLastIter = 0 # when was gcov analysis last performed (in iterations)

    print "Setup fuzzing.."
    signal.signal(signal.SIGINT, signal_handler)

    # setup 
    config["threadId"] = threadId
    config["target_port"] = config["baseport"] + config["threadId"]
    setupEnvironment(config)
    printConfig(config)

    # start server
    startServer(config)
    testServerConnection(config)

    print "Start fuzzing..."

    startTime = time.time()
    epochCount = 0
    while True:
        # stats
        currTime = time.time()
        diffTime = currTime - startTime
        if diffTime > 5:
            fuzzps = epochCount / diffTime
            out = "\n T: %i   Fuzz per second: %i   Count: %i    Crash count: %i   " % (threadId, fuzzps, count, crashCount)
            sys.stdout.write(out)
            sys.stdout.flush()
            startTime = currTime
            epochCount = 0
        else: 
            epochCount += 1 

        haveOutcome = False

        # Step 2: Choose an input file
        inFile = chooseInput(config)

        # Step 3: Generate a seed
        seed = generateSeed(config)

        # Generate a name for the output file
        outExt = os.path.splitext(inFile)[1]
        outFile = os.path.join(config["temp_dir"], str(seed) + outExt)

        # Step 4: Run fuzzer
        runFuzzer(config, inFile, seed, outFile, count)

        # Send to server
        # if it has crashed, the previous seed made it
        if not sendDataToServer(config, outFile):
            handlePrevCrash(config, outExt, inFile, outcome, runFuzzer, handleOutcome)
            haveOutcome = True
            crashCount += 1
            startServer(config)

        # check if crash (does not really work)
        if not haveOutcome and not isAlive(): 
            getServerCrashInfo(config, outFile)
            handleOutcome(config, outcome, inFile, seed, outFile, count)
            haveOutcome = True
            crashCount += 1

            startServer(config)

        # try to restart
        if count > 0 and count % 10000 == 0:
            print "Restart server"
            if not testServerConnection(config):
                handlePrevCrash(config, outExt, inFile, outcome, runFuzzer, handleOutcome)
                crashCount += 1

            stopServer()
            time.sleep(1)
            startServer(config)

        # Delete the output file
        try:
            os.remove(outFile)
        except:
            print "Failed to remove file %s!" % outFile

        # save current state in case we detect a crash on next iteration
        GLOBAL["prev_count"] = count
        GLOBAL["prev_seed"] = seed

        # Update the counter and display the visual feedback
        count += 1

    # all done, terminate server
    stopServer()
    
