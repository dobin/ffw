#!/usr/local/bin/python

import signal
import time
import logging
import queue
import random
import sys

import servermanager
import fuzzingiterationdata
import networkmanager

GLOBAL_SLEEP = {
    # how long to wait after server start
    # can be high as it is not happening so often
    "sleep_after_server_start": 1,

    # send update interval from child to parent
    # via queue
    "communicate_interval": 3
}


def updateStats(iterStats, queue, threadId):
    # stats
    iterStats["currTime"] = time.time()
    iterStats["diffTime"] = iterStats["currTime"] - iterStats["startTime"]
    if iterStats["diffTime"] > GLOBAL_SLEEP["communicate_interval"]:
        iterStats["fuzzps"] = iterStats["epochCount"] / iterStats["diffTime"]
        # send fuzzing information to parent process
        queue.put( (threadId, iterStats["fuzzps"], iterStats["count"], iterStats["crashCount"]) )
        iterStats["startTime"] = iterStats["currTime"]
        iterStats["epochCount"] = 0
    else:
        iterStats["epochCount"] += 1

    #if iterStats.crashCountAnalLast + config["crash_minimize_time"] < iterStats.crashCount:
    #    minimizeCrashes(config)
    #    iterStats.crashCountAnalLast = crashCount


def signal_handler(signal, frame):
    # TODO fixme make object so i can kill server
    #stopServer()
    sys.exit(0)


# Fuzzer child
# The main fuzzing loop
# all magic is performed here
# sends results via queue to the parent
def doActualFuzz(config, threadId, queue, initialSeed):
    global GLOBAL_SLEEP

    random.seed(initialSeed)
    logging.info("Setup fuzzing..")
    signal.signal(signal.SIGINT, signal_handler)
    targetPort = config["baseport"] + threadId
    serverManager = servermanager.ServerManager(config, threadId, targetPort)
    networkManager = networkmanager.NetworkManager(config, targetPort)

    iterStats = {
        "count": 0,
        "crashCount": 0, # number of crashes, absolute
        "crashCountAnalLast": 0, # when was the last crash analysis
        "gcovAnalysisLastIter": 0, # when was gcov analysis last performed (in iterations)
        "startTime": time.time(),
        "epochCount": 0,
    }
    initialData = config["_inputs"]
    sendDataResult = None
    previousFuzzingIterationData = None
    printFuzzData(initialData)

    # start server
    serverManager.start()
    if not networkManager.testServerConnection():
        logging.error("Error")
        return

    print str(threadId) + " Start fuzzing..."
    queue.put( (threadId, 0, 0, 0) )

    while True:
        updateStats(iterStats, queue, threadId)
        logging.debug("\n\n")
        logging.debug("A fuzzing loop...")

        # previous fuzz generated a crash
        if not networkManager.openConnection():
            logging.info("Detected Crash (A)")
            iterStats["crashCount"] += 1
            crashData = serverManager.getCrashData()
            crashData["fuzzerPos"] = "A"
            previousFuzzingIterationData.export(crashData)
            serverManager.restart()
            continue

        fuzzingIterationData = fuzzingiterationdata.FuzzingIterationData(config, initialData)
        if not fuzzingIterationData.fuzzData():
            logging.error("Could not fuzz the data")
            return

        sendDataResult = sendPreData(networkManager, fuzzingIterationData)
        if not sendDataResult:
            logging.info("Detected Crash (B)")
            iterStats["crashCount"] += 1
            crashData = serverManager.getCrashData()
            crashData["fuzzerPos"] = "B"
            previousFuzzingIterationData.export(crashData)
            networkManager.closeConnection()
            serverManager.restart()
            continue

        sendDataResult = sendData(networkManager, fuzzingIterationData)
        if not sendDataResult:
            logging.info("Detected Crash (C)")
            iterStats["crashCount"] += 1
            crashData = serverManager.getCrashData()
            crashData["fuzzerPos"] = "C"
            fuzzingIterationData.export(crashData)
            networkManager.closeConnection()
            serverManager.restart()
            continue

        # restart server periodically
        if iterStats["count"] > 0 and iterStats["count"] % config["restart_server_every"] == 0:
            logging.info("Restart server")
            serverManager.restart()
            if not networkManager.testServerConnection():
                logging.error("Error")
                return

        if config["debug"]:
            # lets sleep a bit
            time.sleep(1)

        # save this iteration data for future crashes
        previousFuzzingIterationData = fuzzingIterationData

        # Update the counter and display the visual feedback
        iterStats["count"] += 1

    # all done, terminate server
    serverManager.stopServer()

def printFuzzData(fuzzData):
    for message in fuzzData:
        print "  MSG: " + str(fuzzData.index(message))
        print "    DATA: " + str( len(message["data"]) )
        print "    FROM: " + str( message["from"] )


def sendPreData(networkManager, fuzzingIterationData):
    logging.info("Send pre data: ")
    for message in fuzzingIterationData.fuzzedData:
        if message["from"] != "cli":
            continue

        if message == fuzzingIterationData.choice:
            break;

        logging.debug("  Sending pre message: " + str(fuzzingIterationData.fuzzedData.index(message)))
        ret = networkManager.sendData(message["data"])
        if not ret:
            logging.debug("  server not reachable")
            return False

    return True


def sendData(networkManager, fuzzingIterationData):
    logging.info("Send data: ")
    # skip pre messages
    s = False
    for message in fuzzingIterationData.fuzzedData:
        if message["from"] != "cli":
            continue

        if message == fuzzingIterationData.choice:
            s = True ;

        if s:
            logging.debug("  Sending message: " + str(fuzzingIterationData.fuzzedData.index(message)))
            res = networkManager.sendData(message["data"])
            if res == False:
                return False

    return True
