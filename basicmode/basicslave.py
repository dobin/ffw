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
from target import targetutils


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
        if self.config['use_netnamespace']:
            targetutils.startInNamespace(self.realDoActualFuzz, self.threadId)
        else:
            self.realDoActualFuzz()


    def realDoActualFuzz(self):
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
        if 'use_netnamespace' in self.config and self.config['use_netnamespace']:
            targetPort = self.config["target_port"]
        else:
            targetPort = self.config["target_port"] + self.threadId


        self.corpusManager = CorpusManager(self.config)
        self.corpusManager.loadCorpusFiles()
        if self.corpusManager.getCorpusCount() == 0:
            logging.error("No corpus input data found in: " +
                          self.config['input_dir'])
            return

        mutatorInterface = MutatorInterface(self.config, self.threadId)

        self.serverManager = ServerManager(
            self.config,
            self.threadId,
            targetPort)
        self.networkManager = networkmanager.NetworkManager(self.config, targetPort)

        self.iterStats = {
            "count": 0,  # number of iterations
            "crashCount": 0,  # number of crashes, absolute
            "startTime": time.time(),
            "lastUpdateTime": time.time(),
        }
        sendDataResult = None
        previousCorpusData = None

        # If we do not manage the server by ourselfs, disable it
        if 'disableServer' in self.config and self.config['disableServer']:
            self.serverManager.dis()
        else:
            self.serverManager.start()

        if not self.networkManager.waitForServerReadyness():
            logging.error("Error: Could not connect to server.")
            # TODO: better error, because server could not be started. stdout?
            return

        print(str(self.threadId) + " Start fuzzing...")
        self.queue.put( (self.threadId, 0, 0, 0) )

        corpusData = None
        while True:
            self.updateStats()
            logging.debug("\n\n")
            logging.debug("A fuzzing loop...")

            if self.config["debug"]:
                # lets sleep a bit
                time.sleep(0.5)

            selectedCorpusData = self.corpusManager.getRandomCorpus()

            # save this iteration data for future crashes
            # we do this at the start, not at the end, so we have to
            # only write it once
            previousCorpusData = corpusData
            corpusData = None

            # previous fuzz generated a crash
            if not self.networkManager.openConnection():
                if previousCorpusData is None:
                    logging.warn("Detected crash, but we didnt yet send any bad data?!")
                    continue

                self._handleCrash(previousCorpusData, 'A')
                continue

            corpusData = mutatorInterface.fuzz(selectedCorpusData)

            sendDataResult = self.networkManager.sendPartialPreData(
                corpusData.networkData)
            if not sendDataResult:
                logging.info(" B Could not send, possible crash? (predata)")
                if self.networkManager.testServerConnection():
                    logging.info(" B Broken connection... continue")
                    self.networkManager.closeConnection()
                    continue
                else:
                    # TODO really previousCorpusData? i think so
                    self._handleCrash(previousCorpusData, 'B')
                    self.networkManager.closeConnection()
                    self.serverManager.restart()
                    continue

            sendDataResult = self.networkManager.sendPartialPostData(
                corpusData.networkData)
            if not sendDataResult:
                logging.info(" C Could not send, possible crash? (postdata)")
                if self.networkManager.testServerConnection():
                    logging.info("C Broken connection... continue")
                    self.networkManager.closeConnection()
                    continue
                else:
                    self._handleCrash(corpusData, 'C')
                    self.networkManager.closeConnection()
                    continue

            # restart server periodically
            if (self.iterStats["count"] > 0 and
                    self.iterStats["count"] % self.config["restart_server_every"] == 0):

                if not self.networkManager.testServerConnection():
                    self._handleCrash(corpusData, 'D')
                    self.networkManager.closeConnection()

                logging.info("Restart server periodically: " +
                             str(self.iterStats["count"]))
                self.serverManager.restart()
                if not self.networkManager.testServerConnection():
                    logging.error("Error: Could not connect to server after restart. abort.")
                    return

                if self.iterStats['count'] > 0 and self.iterStats['count'] % 300 == 0:
                    self.networkManager.tuneTimeouts( self.corpusManager.getMaxLatency() )

        # all done, terminate server
        self.serverManager.stopServer()


    def printFuzzData(self, fuzzData):
        for message in fuzzData:
            print("  MSG: " + str(fuzzData.index(message)))
            print("    DATA: " + str( len(message["data"]) ))
            print("    FROM: " + str( message["from"] ))


    def updateStats(self):
        """Regularly send our statistics to the master."""
        self.iterStats["count"] += 1
        updateInterval = 5

        # check if we should notify parent
        currTime = time.time()
        diffTime = currTime - self.iterStats["lastUpdateTime"]

        if diffTime > updateInterval:
            fuzzPerSec = (float(self.iterStats["count"]) /
                          float(currTime - self.iterStats["startTime"]))
            # send fuzzing information to parent process
            self.queue.put( (
                self.threadId,
                fuzzPerSec,
                self.iterStats["count"],
                self.iterStats["crashCount"],
                self.corpusManager.getMaxLatency()) )

            if "fuzzer_nofork" in self.config and self.config["fuzzer_nofork"]:
                print("%d: %4.2f  %8d  %5d" % (
                      self.threadId,
                      fuzzPerSec,
                      self.iterStats["count"],
                      self.iterStats["crashCount"]
                      ) )

            self.iterStats["lastUpdateTime"] = currTime


    def _handleCrash(self, corpusData, fuzzerPos):
        print("Detected Crash at " + fuzzerPos)
        self.iterStats["crashCount"] += 1
        crashData = CrashData(self.config, corpusData, fuzzerPos)
        self.serverManager.getCrashInformation(crashData)
        crashData.writeToFile()
        self.serverManager.restart()
