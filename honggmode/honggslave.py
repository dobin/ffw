#!/usr/bin/env python2

import signal
import time
import logging
import random
import sys
import pickle
import os
import subprocess

from fuzzer.fuzzingcrashdata import FuzzingCrashData
from network import networkmanager

from fuzzer.fuzzingiterationdata import FuzzingIterationData
from . import honggcomm



def signal_handler(signal, frame):
    # TODO fixme make object so i can kill server
    #stopServer()
    sys.exit(0)


class HonggSlave(object):
    def __init__(self, config, threadId, queue, initialSeed):
        self.config = config
        self.queue = queue
        self.threadId = threadId
        self.initialSeed = initialSeed
        self.iterStats = {
            "lastUpdate": 0,
            "iterCount": 0,
            "corpusCount": 0,
            "crashCount": 0,
        }


    def doActualFuzz(self):
        """
        The main fuzzing loop.

        all magic is performed here
        sends results via queue to the parent
        """
        logging.basicConfig(level=logging.DEBUG)
        self.config["processes"] = 1

        random.seed(self.initialSeed)
        logging.info("Setup fuzzing..")
        signal.signal(signal.SIGINT, signal_handler)
        targetPort = self.config["baseport"] + self.threadId
        self.targetPort = targetPort

        initialData = self.config["_inputs"]
        networkManager = networkmanager.NetworkManager(self.config, targetPort)
        corpus = []
        corpus.append(initialData)

        # start honggfuzz with target binary
        self.startServer()

        # connect with honggfuzz
        honggComm = honggcomm.HonggComm()
        honggComm.openSocket()

        fuzzingIterationData = None
        while True:
            logging.debug("A fuzzing loop...")
            self.manageStats()

            honggData = honggComm.readSocket()

            if honggData == "Fuzz":
                self.iterStats["iterCount"] += 1
                c = random.randint(0, len(corpus) - 1)
                logging.info("--[ Fuzz corpus: " + str(c) + "  size: " + str(len(corpus)))
                idata = corpus[c]
                fuzzingIterationData = FuzzingIterationData(self.config, idata)

                if not fuzzingIterationData.fuzzData():
                    logging.error("Could not fuzz the data")
                    return

                if networkManager.openConnection():
                    self.sendData(networkManager, fuzzingIterationData)
                    networkManager.closeConnection()
                else:
                    logging.error( "--- WTF")

                honggComm.writeSocket("okay")

            elif honggData == "New!":
                logging.info( "--[ Adding file to corpus...")
                corpus.append(fuzzingIterationData.fuzzedData)
                self.iterStats["corpusCount"] += 1
            elif honggData == "Cras":
                logging.info( "--[ Adding crash...")
                self.handleCrash(fuzzingIterationData)
                self.iterStats["crashCount"] += 1
            elif honggData == "":
                logging.info("Hongfuzz quit, exiting too\n")
                break
            else:
                logging.error( "--[ Unknown: " + str(honggData))


    def manageStats(self):
        currTime = time.time()

        if currTime > self.iterStats["lastUpdate"] + 1:
            # send fuzzing information to parent process
            self.queue.put(
                (self.threadId,
                 self.iterStats["iterCount"],
                 self.iterStats["corpusCount"],
                 self.iterStats["crashCount"]) )
            self.iterStats["lastUpdate"] = currTime


    def startServer(self):
        logging.debug( "Starting server")

        args = "/home/dobin/honggfuzz/honggfuzz -Q -S -C -n 1 -d 4 -l log3.txt -s --socket_fuzzer -- "
        args += self.config["target_bin"] + " " + self.config["target_args"] % ( { "port": self.targetPort } )
        argsArr = args.split(" ")
        cmdArr = [ ]
        cmdArr.extend( argsArr )
        popenArg = cmdArr

        logging.info("Starting server with args: " + str(popenArg))

        os.chdir( self.config["projdir"] + "/bin")
        # create devnull so we can us it to surpress output of the server (2.7 specific)
        DEVNULL = open(os.devnull, 'wb')
        try:
            p = subprocess.Popen(popenArg, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
        except Exception as e:
            logging.debug( "E: " + str(e))
            sys.exit(1)
        #time.sleep( 1 )  # wait a bit so we are sure server is really started
        logging.info("  Pid: " + str(p.pid) )


    def sendData(self, networkManager, fuzzingIterationData):
        logging.info("Send data: ")

        for message in fuzzingIterationData.fuzzedData:
            if message["from"] == "srv":
                r = networkManager.receiveData(message)
                if not r:
                    #logging.info("Could not read, crash?!")
                    return False

            if message["from"] == "cli":
                logging.debug("  Sending message: " + str(fuzzingIterationData.fuzzedData.index(message)))
                res = networkManager.sendData(message)
                if res is False:
                    return False

        return True


    def handleCrash(self, fuzzingIterationData):
        srvCrashData = {
            'asanOutput': 'empty',
            'signum': 0,
            'exitcode': 0,
            'reallydead': 0,
            'serverpid': 0,
        }
        crashData = FuzzingCrashData(srvCrashData)
        crashData.setFuzzerPos("-")
        self.exportFuzzResult(crashData, fuzzingIterationData)


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
