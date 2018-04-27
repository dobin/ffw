#!/usr/bin/env python2

import signal
import time
import logging
import random
import sys

from network import networkmanager
from common.corpusmanager import CorpusManager
from mutator.mutatorinterface import MutatorInterface
from target.servermanager import ServerManager
from common.crashdata import CrashData

import utils


def signal_handler(signal, frame):
    # TODO fixme make object so i can kill server
    #stopServer()
    sys.exit(0)


class BasicSlave(object):
    def __init__(self, config, threadId, queue, initialSeed):
        self.config = config
        self.queue = queue
        self.threadId = threadId
        self.initialSeed = initialSeed


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
        targetPort = self.config["target_port"] + self.threadId

        corpusManager = CorpusManager(self.config)
        corpusManager.loadCorpusFiles()

        mutatorInterface = MutatorInterface(self.config)

        serverManager = ServerManager(
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
        previousCorpusData = None

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

        corpusData = None
        while True:
            self.updateStats(iterStats)
            logging.debug("\n\n")
            logging.debug("A fuzzing loop...")

            if self.config["debug"]:
                # lets sleep a bit
                time.sleep(0.5)

            selectedCorpusData = corpusManager.getRandomCorpus()

            # save this iteration data for future crashes
            # we do this at the start, not at the end, so we have to
            # only write it once
            previousCorpusData = corpusData
            corpusData = None

            # previous fuzz generated a crash
            if not networkManager.openConnection():
                logging.info("Detected Crash (A)")
                iterStats["crashCount"] += 1
                crashData = CrashData(self.config, previousCorpusData, 'A')
                serverManager.getCrashInformation(crashData)
                crashData.writeToFile()
                serverManager.restart()
                continue

            corpusData = mutatorInterface.fuzz(selectedCorpusData)

            sendDataResult = networkManager.sendPartialPreData(corpusData.networkData)
            if not sendDataResult:
                logging.info(" B Could not send, possible crash? (predata)")
                if networkManager.testServerConnection():
                    logging.info(" B Broken connection... continue")
                    networkManager.closeConnection()
                    continue
                else:
                    logging.info("Detected Crash (B)")
                    iterStats["crashCount"] += 1
                    # TODO really previousCorpusData? i think so
                    crashData = CrashData(self.config, previousCorpusData, 'B')
                    serverManager.getCrashInformation(crashData)
                    crashData.writeToFile()
                    networkManager.closeConnection()
                    serverManager.restart()
                    continue

            sendDataResult = networkManager.sendPartialPostData(corpusData.networkData)
            if not sendDataResult:
                logging.info(" C Could not send, possible crash? (postdata)")
                if networkManager.testServerConnection():
                    logging.info("C Broken connection... continue")
                    networkManager.closeConnection()
                    continue
                else:
                    logging.info("Detected Crash (C)")
                    iterStats["crashCount"] += 1
                    crashData = CrashData(self.config, corpusData, 'C')
                    serverManager.getCrashInformation(crashData)
                    crashData.writeToFile()
                    networkManager.closeConnection()
                    serverManager.restart()
                    continue

            # restart server periodically
            if iterStats["count"] > 0 and iterStats["count"] % self.config["restart_server_every"] == 0:
                if not networkManager.testServerConnection():
                    logging.info("Detected Crash (D)")
                    iterStats["crashCount"] += 1
                    crashData = CrashData(self.config, corpusData, 'D')
                    serverManager.getCrashInformation(crashData)
                    crashData.writeToFile()
                    networkManager.closeConnection()

                logging.info("Restart server periodically: " + str(iterStats["count"]))
                serverManager.restart()
                if not networkManager.testServerConnection():
                    logging.error("Error: Could not connect to server after restart. abort.")
                    return

        # all done, terminate server
        serverManager.stopServer()


    def printFuzzData(self, fuzzData):
        for message in fuzzData:
            print("  MSG: " + str(fuzzData.index(message)))
            print("    DATA: " + str( len(message["data"]) ))
            print("    FROM: " + str( message["from"] ))


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

            if "fuzzer_nofork" in self.config and self.config["fuzzer_nofork"]:
                print("%d: %4.2f  %8d  %5d" % (self.threadId, fuzzPerSec, iterStats["count"], iterStats["crashCount"]))

            iterStats["lastUpdateTime"] = currTime
