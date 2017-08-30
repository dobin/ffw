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
    "communicate_interval": 3
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
    runTarget=_runTarget,
    checkForCrash=_checkForCrash

    global GLOBAL_SLEEP

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
        readFuzzedData = _readFuzzedDataRaw
    elif config["mode"] == "interceptor":
        chooseInput = _chooseInputInterceptor
        sendDataToServer = network.sendDataToServerInterceptor
        readFuzzedData = _readFuzzedDataInterceptor

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

        # Step 2: Choose an input file / msg
        fuzzIterConfig = chooseInput(config)

        # fuzz and load again
        fuzzInputData(config, fuzzIterConfig, readFuzzedData)

        # Send to server
        # if it has crashed, the previous seed made it crash. handle it.
        if not sendDataToServer(config, fuzzIterConfig):
            handlePrevCrash(config, GLOBAL["prev_fuzzIterConfig"], outcome)
            haveOutcome = True
            crashCount += 1
            startServer(config)

        # check if server crashed (does not really work ?)
        if not haveOutcome and not isAlive():
            handleOutcome(config, outcome, fuzzIterConfig["inFile"], fuzzIterConfig["seed"], fuzzIterConfig["outFile"], count, fuzzIterConfig)
            haveOutcome = True
            crashCount += 1
            startServer(config)

        # restart server periodically
        if count > 0 and count % 10000 == 0:
            print "Restart server"
            if not network.testServerConnection(config):
                handlePrevCrash(config, fuzzIterConfig, outcome)
                crashCount += 1

            stopServer()
            time.sleep(GLOBAL_SLEEP["sleep_after_server_start"])
            startServer(config)
            time.sleep(GLOBAL_SLEEP["sleep_after_server_start"])

        if config["debug"]:
            # lets sleep a bit
            time.sleep(3)

        # save current state in case we detect a crash on next iteration
        GLOBAL["prev_count"] = count
        GLOBAL["prev_seed"] = fuzzIterConfig["seed"]
        GLOBAL["prev_fuzzIterConfig"] = fuzzIterConfig

        # Update the counter and display the visual feedback
        count += 1

    # all done, terminate server
    stopServer()


def fuzzInputData(config, fuzzIterConfig, readFuzzedData):
    # Step 3: Generate a seed
    seed = _generateSeed(config)
    fuzzIterConfig["seed"] = seed

    # Generate a name for the output file
    outExt = os.path.splitext(fuzzIterConfig["inFile"])[1]
    outFile = os.path.join(config["temp_dir"], str(seed) + outExt)

    fuzzIterConfig["outExt"] = outExt
    fuzzIterConfig["outFile"] = outFile

    # Step 4: Run fuzzer process
    _runFuzzer(config, fuzzIterConfig["inFile"], seed, outFile)

    # Read result back
    file = open(outFile, "r")
    data = file.read()
    file.close()
    readFuzzedData(config, fuzzIterConfig, data)

    # Delete the output file
    try:
        os.remove(outFile)
    except:
        print "Failed to remove file %s!" % outFile


def _setupEnvironment(config):
    """
    Performs one-time setup tasks before starting the fuzzer
    """
    # Silence warnings from the ptrace library
    #logging.getLogger().setLevel(logging.ERROR)

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

    fuzzIterConfig = {
        "inFile": os.path.join(config["inputs"], random.choice(_inputs)),
    }

    return fuzzIterConfig


def _readFuzzedDataRaw(config, fuzzIterConfig, data):
    fuzzIterConfig["data"] = data


def _chooseInputInterceptor(config):
    # TODO make this nicer..
    choice = random.choice(config["_inputs"])
    while choice["from"] != "cli":
        choice = random.choice(config["_inputs"])

    logging.debug("selected input: " + str(choice["data"]))

    fuzzIterConfig = {
        "inFile": choice["filename"],
        "current_choice": choice.copy(),
    }

    return fuzzIterConfig


def _readFuzzedDataInterceptor(config, fuzzIterConfig, data):
    fuzzIterConfig["data"] = data

#    logging.debug("  Original data: " + str(fuzzIterConfig["current_choice"]["data"]))
#    logging.debug("  Fuzzed data:   " + str(data))

    fuzzIterConfig["repro"] = list(config["_inputs"])
    m = fuzzIterConfig["repro"].index(fuzzIterConfig["current_choice"])
    fuzzIterConfig["repro"][m]["data"] = data
#    logging.debug("  Fuzzed data:   " + str(fuzzIterConfig["repro"]))


def _generateSeed(config):
    """
    Generate a random seed to pass to the fuzzer
    """
    return random.randint(0, 2**64 - 1)


def _runFuzzer(config, inputFile, seed, outputFile):
    """
    Run the fuzzer specified in the configuration
    """
    fuzzerData = fuzzers[ config["fuzzer"] ]
    if not fuzzerData:
        print "Could not find fuzzer with name: " + config["fuzzer"]
        return False

    args = fuzzerData["args"] % ({
        "seed" : seed,
        "input" : inputFile,
        "output" : outputFile})
    subprocess.call(config["basedir"] + "/" + fuzzerData["file"] + " " + args, shell=True)

    return True


def _checkForCrash(config, event):
    """
    Check if the target application has crashed
    """
    # Normal exits have no signal associated with them
    if event.signum is not None or event.exitcode != 0:
        return event

    return None


def handleOutcome(config, event, inputFile, seed, outputFile, count, fuzzIterConfig):
    """
    Save the output from the fuzzer for replay and make a note of the outcome
    """

    logging.info("Handle Outcome")
    asanOutput = bin_crashes.getAsanOutput(config, GLOBAL["process"].pid)
    
    with open(os.path.join(config["outcome_dir"], str(seed)+".pickle"), "w") as f:
        pickle.dump(fuzzIterConfig["current_choice"], f)

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
    logging.info("Starting server with args: " + str(popenArg))

    # create devnull so we can us it to surpress output of the server (2.7 specific)
    DEVNULL = open(os.devnull, 'wb')
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


def handlePrevCrash(config, fuzzIterConfig, outcome):
#def handlePrevCrash(config, fuzzIterConfig, outExt, inFile, outcome, runFuzzer, handleOutcome):
    # regenerate old outFile

    logging.info("Handle Previus Crash")

    outExt = fuzzIterConfig["outExt"]
    inFile = fuzzIterConfig["inFile"]

    # old filename
    outFilePrev = os.path.join(config["temp_dir"], str(GLOBAL["prev_seed"]) + outExt)

    # start fuzzer with previous seed
    _runFuzzer(config, inFile, GLOBAL["prev_seed"], outFilePrev)

    # handle the result
    handleOutcome(config, outcome, inFile, GLOBAL["prev_seed"], outFilePrev, GLOBAL["prev_count"], fuzzIterConfig)
