# FFW - Fuzzing For Worms
# Author: Dobin Rutishauser
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
import logging
import glob

from multiprocessing import Process, Queue

import bin_crashes

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

    # Most important is to set log_path so we have access to the asan logs
    asanOpts = "" 
    asanOpts += "color=never:verbosity=0:leak_check_at_exit=false:" 
    asanOpts += "abort_on_error=true:log_path=" + config["temp_dir"] + "/asan"
    os.environ["ASAN_OPTIONS"] = asanOpts

    # Tell Glibc to abort on heap corruption but not dump a bunch of output
    os.environ["MALLOC_CHECK_"] = "2"


# create an array of the binary path and its parameters
# used to start the process with popen() etc. 
def getInvokeTargetArgs(config):
    args = config["target_args"] % ( { "port": config["target_port"] } )
    argsArr = args.split(" ")
    cmdArr = [ config["target_bin"] ] 
    cmdArr.extend( argsArr )
    return cmdArr


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
        f.write("Time: %s\n" % time.strftime("%c"))


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
    print "Config for thread:  " + str(config["threadId"])
    print "  Running fuzzer:   ", config["fuzzer"]
    print "  Outcomde dir:     ", config["outcome_dir"]
    print "  Target:           ", config["target_bin"]
    print "  Target port:      ", str(config["target_port"])
    print "  Input dir:        ", config["inputs"]
    print "  Analyze response: ", config["response_analysis"]
    

def _runTarget(config):
    popenArg = getInvokeTargetArgs(config)
    # create devnull so we can us it to surpress output of the server (2.7 specific)
    DEVNULL = open(os.devnull, 'wb')
    p = subprocess.Popen(popenArg, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
    time.sleep(1) # wait a bit so we are sure server is really started
    return p


def startServer(config):
    p = _runTarget(config)
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

    if config["sendInitialDataFunction"] is not None:
        config["sendInitialDataFunction"](sock)

    # sock.setblocking(0)
    file = open(file, "r")
    data = file.read()

    try: 
        sock.sendall(data)
    except socket.error, exc:
        return False

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


def handlePrevCrash(config, outExt, inFile, outcome, runFuzzer, handleOutcome):
    # regenerate old outFile

    # old filename
    outFilePrev = os.path.join(config["temp_dir"], str(GLOBAL["prev_seed"]) + outExt)

    # start fuzzer with previous seed
    runFuzzer(config, inFile, GLOBAL["prev_seed"], outFilePrev, GLOBAL["prev_count"])

    # handle the result 
    handleOutcome(config, outcome, inFile, GLOBAL["prev_seed"], outFilePrev, GLOBAL["prev_count"])


def minimizeCrashes(config): 
    pass




def replayFindFile(config, index):
    outcomes = sorted(glob.glob(os.path.join(config["outcome_dir"], '*.raw')), key=os.path.getctime)
    return outcomes[int(index)]


def replay(config, port, file):
    if file.isdigit():
        file = replayFindFile(config, file)

    config["target_port"] = int(port)
    print "File: " + file
    return sendDataToServer(config, file)


def replayall(config, port):
    print "Replay all files from directory: " + config["outcome_dir"]

    outcomes = sorted(glob.glob(os.path.join(config["outcome_dir"], '*.raw')), key=os.path.getctime)
    n = 0
    for outcome in outcomes: 
        time.sleep(1) # this is required, or replay is fucked. maybe use keyboard?
        sys.stdout.write("%5d: " % n)
        if not replay(config, port, outcome):
            print "could not connect"
            break
        n += 1


# start subprocesses
# this is the main entry point for project fuzzers
def doFuzz(config):
    q = Queue()
    # have to remove sigint handler before forking children
    # so ctlr-c works
    orig = signal.signal(signal.SIGINT, signal.SIG_IGN)

    procs = []
    n = 0
    while n < config["processes"]:
        print "Start child: " + str(n)
        p = Process(target=doActualFuzz, args=(config, n, q))
        procs.append(p)
        p.start()
        n += 1

    # restore signal handler
    signal.signal(signal.SIGINT, orig)

    while True: 
        try: 
            r = q.get()
            print "%d: %4d  %8d  %5d" % r
        except KeyboardInterrupt:
            # handle ctrl-c
            for p in procs: 
                p.terminate()
                p.join()

            break

    print("Finished")


# The main fuzzing loop
# all magic is performed here
def doActualFuzz(config, threadId, queue):
    setupEnvironment=_setupEnvironment
    chooseInput=_chooseInput
    generateSeed=_generateSeed
    runFuzzer=_runFuzzer
    runTarget=_runTarget,
    checkForCrash=_checkForCrash
    handleOutcome=_handleOutcome

    seed = 0
    count = 0
    outcome = None
    crashCount = 0 # number of crashes, absolute
    crashCountAnalLast = 0 # when was the last crash analysis
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

    print str(threadId) + " Start fuzzing..."

    startTime = time.time()
    epochCount = 0
    while True:
        # stats
        currTime = time.time()
        diffTime = currTime - startTime
        if diffTime > 5:
            fuzzps = epochCount / diffTime
            # send fuzzing information to parent process
            queue.put( (threadId, fuzzps, count, crashCount) )
            startTime = currTime
            epochCount = 0
        else: 
            epochCount += 1 

        if crashCountAnalLast + config["crash_minimize_time"] < crashCount: 
            minimizeCrashes(config)
            crashCountAnalLast = crashCount

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
        # if it has crashed, the previous seed made it crash. handle it.
        if not sendDataToServer(config, outFile):
            handlePrevCrash(config, outExt, inFile, outcome, runFuzzer, handleOutcome)
            haveOutcome = True
            crashCount += 1
            startServer(config)

        # check if server crashed (does not really work)
        if not haveOutcome and not isAlive(): 
            getServerCrashInfo(config, outFile)
            handleOutcome(config, outcome, inFile, seed, outFile, count)
            haveOutcome = True
            crashCount += 1

            startServer(config)

        # restart server periodically
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
    

def realMain(config):
    func = "fuzz"
    if len(sys.argv) > 1:
        func = sys.argv[1]

    if func == "corpus_destillation":
        corpus_destillation()

    if func == "minimize":
        bin_crashes.minimize(config)

    if func == "replay":
        replay(config, sys.argv[2], sys.argv[3])

    if func == "replayall":
        replayall(config, sys.argv[2])

    if func == "fuzz":
        try:
            doFuzz(config)
        except KeyboardInterrupt as e:
            return 0



def corpus_destillation():
    print "Corpus destillation"

