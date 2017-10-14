#!/usr/bin/env python2

import signal
import time
import logging
import random
import sys
import pickle
import os

from fuzzingcrashdata import FuzzingCrashData
from network import networkmanager
import fuzzingiterationdata
import simpleservermanager

GLOBAL_SLEEP = {
    # how long to wait after server start
    # can be high as it is not happening so often
    "sleep_after_server_start": 1,

    # send update interval from child to parent
    # via queue
    "communicate_interval": 3
}


def signal_handler(signal, frame):
    # TODO fixme make object so i can kill server
    #stopServer()
    sys.exit(0)


class FuzzingSlave(object):
    def __init__(self, config, threadId, queue, initialSeed):
        self.config = config
        self.queue = queue
        self.threadId = threadId
        self.initialSeed = initialSeed


    def updateStats(self, iterStats):
        # stats
        iterStats["currTime"] = time.time()
        iterStats["diffTime"] = iterStats["currTime"] - iterStats["startTime"]
        if iterStats["diffTime"] > GLOBAL_SLEEP["communicate_interval"]:
            iterStats["fuzzps"] = iterStats["epochCount"] / iterStats["diffTime"]
            # send fuzzing information to parent process
            self.queue.put( (self.threadId, iterStats["fuzzps"], iterStats["count"], iterStats["crashCount"]) )
            iterStats["startTime"] = iterStats["currTime"]
            iterStats["epochCount"] = 0
        else:
            iterStats["epochCount"] += 1

        #if iterStats.crashCountAnalLast + config["crash_minimize_time"] < iterStats.crashCount:
        #    minimizeCrashes(config)
        #    iterStats.crashCountAnalLast = crashCount


    def doActualFuzz(self):
        """
        The main fuzzing loop.

        all magic is performed here
        sends results via queue to the parent
        Only called once, by the fuzzingmaster
        """
        global GLOBAL_SLEEP

        random.seed(self.initialSeed)
        logging.info("Setup fuzzing..")
        signal.signal(signal.SIGINT, signal_handler)
        targetPort = self.config["baseport"] + self.threadId
        serverManager = simpleservermanager.SimpleServerManager(self.config, self.threadId, targetPort)
        networkManager = networkmanager.NetworkManager(self.config, targetPort)

        iterStats = {
            "count": 0,
            "crashCount": 0,  # number of crashes, absolute
            "crashCountAnalLast": 0,  # when was the last crash analysis
            "gcovAnalysisLastIter": 0,  # when was gcov analysis last performed (in iterations)
            "startTime": time.time(),
            "epochCount": 0,
        }
        initialData = self.config["_inputs"]
        sendDataResult = None
        previousFuzzingIterationData = None
        self.printFuzzData(initialData)

        # start server
        serverManager.start()
        if not networkManager.waitForServerReadyness():
            logging.error("Error: Could not connect to server.")
            # TODO: better error, because server could not be started. stdout?
            return

        print str(self.threadId) + " Start fuzzing..."
        self.queue.put( (self.threadId, 0, 0, 0) )

        while True:
            self.updateStats(iterStats)
            logging.debug("\n\n")
            logging.debug("A fuzzing loop...")

            if self.config["debug"]:
                # lets sleep a bit
                time.sleep(0.5)

            # previous fuzz generated a crash
            if not networkManager.openConnection():
                logging.info("Detected Crash (A)")
                iterStats["crashCount"] += 1
                srvCrashData = serverManager.getCrashData()
                crashData = FuzzingCrashData(srvCrashData)
                crashData.setFuzzerPos("A")
                self.exportFuzzResult(crashData, previousFuzzingIterationData)
                serverManager.restart()
                continue

            fuzzingIterationData = fuzzingiterationdata.FuzzingIterationData(self.config, initialData)
            if not fuzzingIterationData.fuzzData():
                logging.error("Could not fuzz the data")
                return

            sendDataResult = self.sendPreData(networkManager, fuzzingIterationData)
            if not sendDataResult:
                logging.info(" B Could not send, possible crash? (predata)")
                if networkManager.testServerConnection():
                    logging.info(" B Broken connection... continue")
                    networkManager.closeConnection()
                    continue
                else:
                    logging.info("Detected Crash (B)")
                    iterStats["crashCount"] += 1
                    srvCrashData = serverManager.getCrashData()
                    crashData = FuzzingCrashData(srvCrashData)
                    crashData.setFuzzerPos("B")
                    self.exportFuzzResult(crashData, fuzzingIterationData)
                    networkManager.closeConnection()
                    serverManager.restart()
                    continue

            sendDataResult = self.sendData(networkManager, fuzzingIterationData)
            if not sendDataResult:
                logging.info(" C Could not send, possible crash? (postdata)")
                if networkManager.testServerConnection():
                    logging.info("C Broken connection... continue")
                    networkManager.closeConnection()
                    continue
                else:
                    logging.info("Detected Crash (C)")
                    iterStats["crashCount"] += 1
                    srvCrashData = serverManager.getCrashData()
                    crashData = FuzzingCrashData(srvCrashData)
                    crashData.setFuzzerPos("C")
                    self.exportFuzzResult(crashData, fuzzingIterationData)
                    networkManager.closeConnection()
                    serverManager.restart()
                    continue

            # restart server periodically
            if iterStats["count"] > 0 and iterStats["count"] % self.config["restart_server_every"] == 0:
                if not networkManager.testServerConnection():
                    logging.info("Detected Crash (D)")
                    iterStats["crashCount"] += 1
                    srvCrashData = serverManager.getCrashData()
                    crashData = FuzzingCrashData(srvCrashData)
                    crashData.setFuzzerPos("D")
                    self.exportFuzzResult(crashData, fuzzingIterationData)
                    networkManager.closeConnection()

                logging.info("Restart server periodically: " + str(iterStats["count"]))
                serverManager.restart()
                if not networkManager.testServerConnection():
                    logging.error("Error: Could not connect to server after restart. abort.")
                    return

            # save this iteration data for future crashes
            previousFuzzingIterationData = fuzzingIterationData

            # Update the counter and display the visual feedback
            iterStats["count"] += 1

        # all done, terminate server
        serverManager.stopServer()


    def printFuzzData(self, fuzzData):
        for message in fuzzData:
            print "  MSG: " + str(fuzzData.index(message))
            print "    DATA: " + str( len(message["data"]) )
            print "    FROM: " + str( message["from"] )


    def sendPreData(self, networkManager, fuzzingIterationData):
        logging.info("Send pre data: ")

        for message in fuzzingIterationData.fuzzedData:
            if message == fuzzingIterationData.choice:
                break

            if message["from"] == "srv":
                r = networkManager.receiveData(message)
                if not r:
                    logging.info("Could not read, crash?!")
                    return False

            if message["from"] == "cli":
                logging.debug("  Sending pre message: " + str(fuzzingIterationData.fuzzedData.index(message)))
                ret = networkManager.sendData(message)
                if not ret:
                    logging.debug("  server not reachable")
                    return False

        return True


    def sendData(self, networkManager, fuzzingIterationData):
        logging.info("Send data: ")

        s = False
        for message in fuzzingIterationData.fuzzedData:
            # skip pre messages
            if message == fuzzingIterationData.choice:
                s = True

            if s:
                if message["from"] == "srv":
                    r = networkManager.receiveData(message)
                    if not r:
                        logging.info("Could not read, crash?!")
                        return False

                if message["from"] == "cli":
                    logging.debug("  Sending message: " + str(fuzzingIterationData.fuzzedData.index(message)))
                    res = networkManager.sendData(message)
                    if res is False:
                        return False

        return True


    def exportFuzzResult(self, crashDataModel, fuzzIter):
        seed = fuzzIter.seed

        crashData = crashDataModel.getData()

        data = {
            "fuzzerCrashData": crashData,
            "fuzzIterData": fuzzIter.getData(),
        }

        # pickle file with everything
        with open(os.path.join(self.config["outcome_dir"], str(seed) + ".ffw"), "w") as f:
            pickle.dump(data, f)

        # Save a txt log
        with open(os.path.join(self.config["outcome_dir"], str(seed) + ".txt"), "w") as f:
            f.write("Seed: %s\n" % seed)
            f.write("Fuzzer: %s\n" % self.config["fuzzer"])
            f.write("Target: %s\n" % self.config["target_bin"])

            f.write("Time: %s\n" % data["fuzzIterData"]["time"])
            f.write("Fuzzerpos: %s\n" % crashData["fuzzerPos"])
            f.write("Signal: %d\n" % crashData["signum"])
            f.write("Exitcode: %d\n" % crashData["exitcode"])
            f.write("Reallydead: %s\n" % str(crashData["reallydead"]))
            f.write("PID: %s\n" % str(crashData["serverpid"]))
            f.write("Asanoutput: %s\n" % crashData["asanOutput"])
