#!/usr/bin/env python2

import signal
import time
import logging
import random
import sys

from .fuzzingcrashdata import FuzzingCrashData
from network import networkmanager
from . import fuzzingiterationdata
from . import simpleservermanager
from common import crashinfo
import utils


def signal_handler(signal, frame):
    # TODO fixme make object so i can kill server
    #stopServer()
    sys.exit(0)


class FuzzingSlave(object):
    def __init__(self, config, threadId, queue, initialSeed, inputs):
        self.config = config
        self.queue = queue
        self.threadId = threadId
        self.initialSeed = initialSeed
        self.inputs = inputs


    def doActualFuzz(self):
        """
        The main fuzzing loop.

        all magic is performed here
        sends results via queue to the parent
        Only called once, by the fuzzingmaster
        """
        if "DebugWithFile" in self.config:
            utils.setupSlaveLoggingWithFile(self.threadId)

        random.seed(self.initialSeed)
        logging.info("Setup fuzzing..")
        signal.signal(signal.SIGINT, signal_handler)
        targetPort = self.config["baseport"] + self.threadId
        serverManager = simpleservermanager.SimpleServerManager(
            self.config,
            self.threadId,
            targetPort)
        networkManager = networkmanager.NetworkManager(self.config, targetPort)

        iterStats = {
            "count": 0,  # number of iterations
            "crashCount": 0,  # number of crashes, absolute
            "startTime": time.time(),
            "lastUpdateTime": time.time(),
        }
        sendDataResult = None
        previousFuzzingIterationData = None

        # If we do not manage the server by ourselfs, disable it
        if 'disableServer' in self.config and self.config['disableServer']:
            serverManager.dis()
        else:
            serverManager.start()

        if not networkManager.waitForServerReadyness():
            logging.error("Error: Could not connect to server.")
            # TODO: better error, because server could not be started. stdout?
            return

        print(str(self.threadId) + " Start fuzzing...")
        self.queue.put( (self.threadId, 0, 0, 0) )

        fuzzingIterationData = None
        while True:
            self.updateStats(iterStats)
            logging.debug("\n\n")
            logging.debug("A fuzzing loop...")

            if self.config["debug"]:
                # lets sleep a bit
                time.sleep(0.5)

            selectedInput = self.selectInput()

            # save this iteration data for future crashes
            # we do this at the start, not at the end, so we have to
            # only write it once
            previousFuzzingIterationData = fuzzingIterationData
            fuzzingIterationData = None

            # previous fuzz generated a crash
            if not networkManager.openConnection():
                logging.info("Detected Crash (A)")
                iterStats["crashCount"] += 1
                srvCrashData = serverManager.getCrashData()
                crashData = FuzzingCrashData(srvCrashData)
                crashData.setFuzzerPos("A")
                crashinfo.exportFuzzResult(
                    crashData,
                    previousFuzzingIterationData,
                    self.config)
                serverManager.restart()
                continue

            fuzzingIterationData = fuzzingiterationdata.FuzzingIterationData(
                self.config,
                selectedInput)
            if not fuzzingIterationData.fuzzData():
                logging.error("Could not fuzz the data")
                return

            sendDataResult = self.sendPreData(
                networkManager,
                fuzzingIterationData)
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
                    # TODO really previousFuzzingIterationData? i think so
                    crashinfo.exportFuzzResult(
                        crashData,
                        previousFuzzingIterationData,
                        self.config)
                    networkManager.closeConnection()
                    serverManager.restart()
                    continue

            sendDataResult = self.sendData(
                networkManager,
                fuzzingIterationData)
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
                    crashinfo.exportFuzzResult(
                        crashData,
                        fuzzingIterationData,
                        self.config)
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
                    crashinfo.exportFuzzResult(
                        crashData,
                        fuzzingIterationData,
                        self.config)
                    networkManager.closeConnection()

                logging.info("Restart server periodically: " + str(iterStats["count"]))
                serverManager.restart()
                if not networkManager.testServerConnection():
                    logging.error("Error: Could not connect to server after restart. abort.")
                    return

        # all done, terminate server
        serverManager.stopServer()


    def selectInput(self):
        return random.choice(self.inputs)


    def printFuzzData(self, fuzzData):
        for message in fuzzData:
            print("  MSG: " + str(fuzzData.index(message)))
            print("    DATA: " + str( len(message["data"]) ))
            print("    FROM: " + str( message["from"] ))


    def sendPreData(self, networkManager, fuzzingIterationData):
        logging.info("Send pre data: ")

        for message in fuzzingIterationData.fuzzedData:
            if message == fuzzingIterationData.choice:
                break

            if message["from"] == "srv":
                r = networkManager.receiveData(message)
                if not r:
                    return False

            if message["from"] == "cli":
                logging.debug("  Sending pre message: " + str(fuzzingIterationData.fuzzedData.index(message)))
                ret = networkManager.sendData(message)
                if not ret:
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
                        return False

                if message["from"] == "cli":
                    if "isFuzzed" in message:
                        logging.debug("  Sending fuzzed message: " + str(fuzzingIterationData.fuzzedData.index(message)))
                    else:
                        logging.debug("  Sending post message: " + str(fuzzingIterationData.fuzzedData.index(message)))
                    res = networkManager.sendData(message)
                    if res is False:
                        return False

        return True


    def updateStats(self, iterStats):
        """Regularly send our statistics to the master"""
        iterStats["count"] += 1
        updateInterval = 5

        # check if we should notify parent
        currTime = time.time()
        diffTime = currTime - iterStats["lastUpdateTime"]

        if diffTime > updateInterval:
            fuzzPerSec = float(iterStats["count"]) / float(currTime - iterStats["startTime"])
            # send fuzzing information to parent process
            self.queue.put( (self.threadId, fuzzPerSec, iterStats["count"], iterStats["crashCount"]) )

            if "nofork" in self.config and self.config["nofork"]:
                print("%d: %4.2f  %8d  %5d" % (self.threadId, fuzzPerSec, iterStats["count"], iterStats["crashCount"]))

            iterStats["lastUpdateTime"] = currTime
