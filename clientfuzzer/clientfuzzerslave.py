#!/usr/bin/env python2

import signal
import time
import logging
import random
import sys
import pickle
import os

from clientmanager import ClientManager
from clientfuzzerserver import ClientFuzzerServer
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
        logging.info("Setup fuzzing...")
        signal.signal(signal.SIGINT, signal_handler)

        targetPort = self.config["target_port"] + self.threadId
        clientManager = ClientManager(self.config, self.threadId, targetPort)
        networkServerManager = ClientFuzzerServer(self.config, targetPort)

        # start the server
        if not networkServerManager.start():
            return

        iterStats = {
            "count": 0,  # number of iterations
            "crashCount": 0,  # number of crashes, absolute
            "startTime": time.time(),
            "lastUpdateTime": time.time(),
        }
        sendDataResult = None

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

            fuzzingIterationData = fuzzingiterationdata.FuzzingIterationData(self.config, selectedInput)
            if not fuzzingIterationData.fuzzData():
                logging.error("Could not fuzz the data")
                return

            networkServerManager.setFuzzData(fuzzingIterationData)
            clientManager.execute()
            networkServerManager.handleConnection()

        networkServerManager.stop()


    def selectInput(self):
        # just randomly select an input for now
        return random.choice(self.inputs)


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


    def exportFuzzResult(self, crashDataModel, fuzzIter):
        """Write information about an identified crash to disk"""
        if crashDataModel is None:
            logging.error("No crash data model. aborting.")
            return
        if fuzzIter is None:
            logging.error("Received None as fuzz iteration. Wrong server-down detection?")
            return

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
