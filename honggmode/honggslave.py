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
from . import corpusmanager


def signal_handler(signal, frame):
    # TODO fixme make object so i can kill server
    #stopServer()
    sys.exit(0)


class HonggSlave(object):
    """
    The child thread of the HonggMode fuzzer.

    Implements the actual fuzzing logic, whereas the HonggMode
    class only starts this class as a dedicated thread.
    """

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
        self.fuzzerPid = None


    def doActualFuzz(self):
        """
        Child thread of fuzzer - does teh actual fuzzing.

        Sends results/stats via queue to the parent.
        Will start the target via honggfuzz, connect to the honggfuzz socket,
        and according to the honggfuzz commands from the socket, send
        the fuzzed messages to the target binary.
        """
        logging.basicConfig(level=logging.DEBUG)
        self.config["processes"] = 1

        logging.info("Setup fuzzing..")
        random.seed(self.initialSeed)
        signal.signal(signal.SIGINT, signal_handler)
        targetPort = self.config["baseport"] + self.threadId
        self.targetPort = targetPort

        networkManager = networkmanager.NetworkManager(self.config, targetPort)
        self.corpusManager = corpusmanager.CorpusManager(self.config)
        self.corpusManager.initialLoad()
        self.corpusManager.startWatch()

        # start honggfuzz with target binary
        self._startServer()

        # connect with honggfuzz
        honggComm = honggcomm.HonggComm()
        honggComm.openSocket(self.fuzzerPid)

        # warmup
        # Send all initial corpus once and ignore new BB commands so we
        # dont add it again.
        # Note that at the end, there may be still commands in the socket
        # queue which we need to ignore on the fuzzing loop.
        initialCorpusIter = iter(self.corpusManager)
        logging.info("Performing warmup")
        while True:
            logging.debug("A warmup loop...")

            try:
                initialCorpusData = initialCorpusIter.next()
            except StopIteration:
                break

            honggData = honggComm.readSocket()
            if honggData == "Fuzz":
                logging.debug("Fuzz: Warmup send")
                self._connectAndSendData(networkManager, initialCorpusData)
                honggComm.writeSocket("okay")

            else:
                # We dont really care what the fuzzer sends us
                # BUT it should be always "New!"
                # It should never be "Cras"
                logging.debug("received: " + honggData)

        # the actual fuzzing
        logging.info("Performing fuzzing")
        fuzzingIterationData = None
        while True:
            logging.debug("A fuzzing loop...")
            self._uploadStats()
            self.corpusManager.checkForNewFiles()

            honggData = honggComm.readSocket()
            if honggData == "Fuzz":
                self.iterStats["iterCount"] += 1

                corpusData = self.corpusManager.getRandomCorpus()
                fuzzingIterationData = FuzzingIterationData(self.config, corpusData)
                if not fuzzingIterationData.fuzzData():
                    logging.error("Could not fuzz the data")
                    return

                self._connectAndSendData(networkManager, fuzzingIterationData.fuzzedData)
                honggComm.writeSocket("okay")

            elif honggData == "New!":
                # Warmup may result in a stray message, ignore here
                if fuzzingIterationData is not None:
                    logging.info( "--[ Adding file to corpus...")
                    self.corpusManager.addNewCorpusFile(fuzzingIterationData.fuzzedData, fuzzingIterationData.seed)
                    self.iterStats["corpusCount"] += 1

            elif honggData == "Cras":
                # Warmup may result in a stray message, ignore here
                if fuzzingIterationData is not None:
                    logging.info( "--[ Adding crash...")
                    self._handleCrash(fuzzingIterationData)
                    self.iterStats["crashCount"] += 1

            elif honggData == "":
                logging.info("Hongfuzz quit, exiting too\n")
                break
            else:
                # This should not happen
                logging.error( "--[ Unknown: " + str(honggData))


    def _connectAndSendData(self, networkManager, data):
        """Connect to server via networkManager and send the data."""
        # try to connect, if server down, wait a bit and try
        # again (forever)
        while not networkManager.openConnection():
            time.sleep(0.2)

        self._sendData(networkManager, data)
        networkManager.closeConnection()


    def _uploadStats(self):
        """Send fuzzing statistics to parent."""
        currTime = time.time()

        if currTime > self.iterStats["lastUpdate"] + 1:
            # send fuzzing information to parent process
            self.queue.put(
                (self.threadId,
                 self.iterStats["iterCount"],
                 self.iterStats["corpusCount"],
                 self.corpusManager.getCorpusCount(),
                 self.iterStats["crashCount"]) )
            self.iterStats["lastUpdate"] = currTime


    def _startServer(self):
        """Start the target (-server) via honggfuzz."""
        logging.debug( "Starting server/honggfuzz")

        args = self.config["honggpath"] + " -Q -S -C -n 1 -d 4 -l log3.txt -s --socket_fuzzer -- "
        args += self.config["target_bin"] + " " + self.config["target_args"] % ( { "port": self.targetPort } )
        argsArr = args.split(" ")
        cmdArr = [ ]
        cmdArr.extend( argsArr )
        popenArg = cmdArr

        logging.info("Starting server/honggfuzz with args: " + str(args))

        os.chdir( self.config["projdir"] + "/bin")
        # create devnull so we can us it to surpress output of the server (2.7 specific)
        DEVNULL = open(os.devnull, 'wb')
        try:
            p = subprocess.Popen(popenArg, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
        except Exception as e:
            logging.debug( "E: " + str(e))
            sys.exit(1)
        time.sleep( 1 )  # wait a bit so we are sure server is really started
        self.fuzzerPid = p.pid


    def _sendData(self, networkManager, messages):
        """Send the (-fuzzed) network messages to the target."""
        logging.info("Send data: ")

        for message in messages:
            if message["from"] == "srv":
                r = networkManager.receiveData(message)
                if not r:
                    #logging.info("Could not read, crash?!")
                    return False

            if message["from"] == "cli":
                logging.debug("  Sending message: " + str(messages.index(message)))
                res = networkManager.sendData(message)
                if res is False:
                    return False

        return True


    def _handleCrash(self, fuzzingIterationData):
        srvCrashData = {
            'asanOutput': 'empty',
            'signum': 0,
            'exitcode': 0,
            'reallydead': 0,
            'serverpid': 0,
        }
        crashData = FuzzingCrashData(srvCrashData)
        crashData.setFuzzerPos("-")
        self._exportFuzzResult(crashData, fuzzingIterationData)


    def _exportFuzzResult(self, crashDataModel, fuzzIter):
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
