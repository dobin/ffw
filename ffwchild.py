#!/usr/local/bin/python

import signal 
import queue
import logging
import os
from multiprocessing import Process, Queue
import subprocess
import time
import random
import shutil
import pickle

import bin_crashes
import network

GLOBAL = {
    "process": 0,
    "prev_seed": 0,
}

GLOBAL_SLEEP = {
    # how long to wait after server start
    # can be high as it is not happening so often
    "sleep_after_server_start": 1,

    # send update interval from child to parent
    # via queue
    "communicate_interval": 3,
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


# Fuzzer child
# The main fuzzing loop
# all magic is performed here
# sends results via queue to the parent
def doActualFuzz(config, threadId, queue):
    setupEnvironment=_setupEnvironment
    generateSeed=_generateSeed
    runFuzzer=_runFuzzer
    runTarget=_runTarget,
    checkForCrash=_checkForCrash
    handleOutcome=_handleOutcome

    global GLOBAL_SLEEP

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

    if config["mode"] == "raw": 
        chooseInput = _chooseInputRaw
        sendDataToServer = network.sendDataToServerRaw
    elif config["mode"] == "interceptor":
        chooseInput = _chooseInputInterceptor
        sendDataToServer = network.sendDataToServerInterceptor

    # start server
    startServer(config)
    network.testServerConnection(config)

    print str(threadId) + " Start fuzzing..."
    queue.put( (threadId, 0, 0, 0) )

    startTime = time.time()
    epochCount = 0
    while True:
        # stats
        currTime = time.time()
        diffTime = currTime - startTime
        if diffTime > GLOBAL_SLEEP["communicate_interval"]:
            fuzzps = epochCount / diffTime
            # send fuzzing information to parent process
            queue.put( (threadId, fuzzps, count, crashCount) )
            startTime = currTime
            epochCount = 0
        else: 
            epochCount += 1 

        if crashCountAnalLast + config["crash_minimize_time"] < crashCount: 
            #minimizeCrashes(config)
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

        # check if server crashed (does not really work ?)
        if not haveOutcome and not isAlive(): 
            handleOutcome(config, outcome, inFile, seed, outFile, count)
            haveOutcome = True
            crashCount += 1
            startServer(config)

        # restart server periodically
        if count > 0 and count % config["server_restart_rate"] == 0:
            print "Restart server"
            if not network.testServerConnection(config):
                handlePrevCrash(config, outExt, inFile, outcome, runFuzzer, handleOutcome)
                crashCount += 1

            stopServer()
            time.sleep(GLOBAL_SLEEP["sleep_after_server_start"])
            startServer(config)
            time.sleep(GLOBAL_SLEEP["sleep_after_server_start"])

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


def _chooseInputRaw(config):
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

def _chooseInputInterceptor(config):
    if not "_inputs" in config:
        with open(config["inputs"] + "/data_0.pickle",'rb') as f:
            config["_inputs"] = pickle.load(f)

            # write all datas to the fs
            n = 0
            for inp in config["_inputs"]:
                fileName = config["inputs"] + "/input_" + str(n) + ".raw"
                file = open(fileName, 'wb')
                file.write(inp["data"])
                file.close()
                inp["filename"] = fileName
                n += 1

    choice = random.choice(config["_inputs"])
    while choice["from"] != "cli": 
        choice = random.choice(config["_inputs"])
        
    config["current_choice"] = choice

    return choice["filename"]


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

    asanOutput = bin_crashes.getAsanOutput(config, GLOBAL["process"].pid)

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

        f.write("Asanoutput: %s\n" % asanOutput)

    # Save the output
    # copy from temp/ to out/. It will be deleted later. 
    try:
        shutil.copy(outputFile, os.path.join(config["outcome_dir"],
            os.path.basename(outputFile)))
    except Exception as e:
        print "Failed to copy output file:", outputFile
        print "E: " + str(e)


def _runTarget(config):
    global GLOBAL_SLEEP
    popenArg = getInvokeTargetArgs(config)
    # create devnull so we can us it to surpress output of the server (2.7 specific)
    DEVNULL = open(os.devnull, 'wb')
    os.chdir(os.path.dirname( config["target_bin"] ))
    p = subprocess.Popen(popenArg, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
    time.sleep( GLOBAL_SLEEP["sleep_after_server_start"] ) # wait a bit so we are sure server is really started
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


def handlePrevCrash(config, outExt, inFile, outcome, runFuzzer, handleOutcome):
    # regenerate old outFile

    # old filename
    outFilePrev = os.path.join(config["temp_dir"], str(GLOBAL["prev_seed"]) + outExt)

    # start fuzzer with previous seed
    runFuzzer(config, inFile, GLOBAL["prev_seed"], outFilePrev, GLOBAL["prev_count"])

    # handle the result 
    handleOutcome(config, outcome, inFile, GLOBAL["prev_seed"], outFilePrev, GLOBAL["prev_count"])
