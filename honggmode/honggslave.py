#!/usr/bin/env python2

import signal
import time
import logging
import random
import sys
import os

from fuzzer.fuzzingcrashdata import FuzzingCrashData
from network import networkmanager
from fuzzer.fuzzingiterationdata import FuzzingIterationData
import utils
from . import honggcomm
from . import corpusmanager
from fuzzer import simpleservermanager
from common import crashinfo


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
            "timeoutCount": 0,
            "startTime": time.time(),
        }
        self.fuzzerPid = None


    def doActualFuzz(self):
        """
        Child thread of fuzzer - does teh actual fuzzing.

        Sends results/stats via queue to the parent.
        Will start the target via honggfuzz, connect to the honggfuzz socket,
        and according to the honggfuzz commands from the socket, send
        the fuzzed messages to the target binary.

        New fuzzed data will be generated via FuzzingIterationData, where
        the initial data from the corpus is managed by CorpusManager.
        """
        #logging.basicConfig(level=logging.DEBUG)
        if "debug" in self.config and self.config["debug"]:
            self.config["processes"] = 1

        if "DebugWithFile" in self.config:
            utils.setupSlaveLoggingWithFile(self.threadId)

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
        honggfuzzArgs = self._prepareHonggfuzzArgs()
        serverManager = simpleservermanager.SimpleServerManager(
            self.config,
            self.threadId,
            targetPort,
            honggfuzzArgs,
            True
        )
        serverManager.start()

        # connect to honggfuzz
        honggComm = honggcomm.HonggComm()
        if honggComm.openSocket(serverManager.process.pid):
            print (" connected!")

        # test connection first
        if not networkManager.debugServerConnection():
            logging.error("Damn.")
            return

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

        # Just assume target is alive, because of the warmup phase
        # this var is needed mainly to not create false-positives, e.g.
        # if the target is for some reason unstartable, it would be detected
        # as crash
        haveCheckedTargetIsAlive = True

        while True:
            logging.debug("A fuzzing loop...")
            self._uploadStats()
            self.corpusManager.checkForNewFiles()
            honggData = None

            try:
                honggData = honggComm.readSocket()
            except Exception as e:
                logging.error("Could not read from honggfuzz socket: " + str(e))
                logging.error("Honggfuzz server crashed? Killed?")
                return

            # honggfuzz says: Send fuzz data via network
            if honggData == "Fuzz":
                couldSend = False

                # are we really sure that the target is alive? If not, check
                if not haveCheckedTargetIsAlive:
                    if not networkManager.waitForServerReadyness():
                        logging.error("Wanted to fuzz, but targets seems down. Force honggfuzz to restart it.")
                        honggComm.writeSocket("bad!")
                        self.iterStats["timeoutCount"] += 1
                    else:
                        haveCheckedTargetIsAlive = True

                # check first if we have new corpus from other threads
                # if yes: send it. We'll ignore New!/Cras msgs by setting:
                #   fuzzingIterationData = None
                if self.corpusManager.hasNewExternalCorpus():
                    fuzzingIterationData = None  # ignore results
                    corpus = self.corpusManager.getNewExternalCorpus()
                    corpus.processed = True
                    couldSend = self._connectAndSendData(networkManager, corpus.getData())

                # just randomly select a corpus, fuzz it, send it
                # honggfuzz will tell us what to do next
                else:
                    self.iterStats["iterCount"] += 1

                    corpus = self.corpusManager.getRandomCorpus()
                    fuzzingIterationData = FuzzingIterationData(self.config, corpus.getData(), corpus)
                    if not fuzzingIterationData.fuzzData():
                        logging.error("Could not fuzz the data")
                        return

                    couldSend = self._connectAndSendData(networkManager, fuzzingIterationData.fuzzedData)

                if couldSend:
                    # Notify honggfuzz that we are finished sending the fuzzed data
                    honggComm.writeSocket("okay")

                    # the correct way is to send SIGIO signal to honggfuzz
                    # https://github.com/google/honggfuzz/issues/200
                    os.kill(serverManager.process.pid, signal.SIGIO)
                else:
                    # target seems to be down. Have honggfuzz restart it
                    # and hope for the best, but check after restart if it
                    # is really up
                    logging.info("Server appears to be down, force restart")
                    self.iterStats["timeoutCount"] += 1
                    honggComm.writeSocket("bad!")
                    haveCheckedTargetIsAlive = False

            # honggfuzz says: new basic-block found
            #   (from the data we sent before)
            elif honggData == "New!":
                # Warmup may result in a stray message, ignore here
                # If new-corpus-from-other-thread: Ignore here
                if fuzzingIterationData is not None:
                    logging.info( "--[ Adding file to corpus...")
                    self.corpusManager.addNewCorpus(fuzzingIterationData.fuzzedData, fuzzingIterationData.seed)
                    fuzzingIterationData.getParentCorpus().statsAddNew()

                    self.iterStats["corpusCount"] += 1

            # honggfuzz says: target crashed (yay!)
            elif honggData == "Cras":
                # Warmup may result in a stray message, ignore here
                # If new-corpus-from-other-thread: Ignore here
                if fuzzingIterationData is not None:
                    logging.info( "--[ Adding crash...")
                    self._handleCrash(fuzzingIterationData)
                    self.iterStats["crashCount"] += 1

                # target was down and needs to be restarted by honggfuzz.
                # check if it was successfully restarted!
                haveCheckedTargetIsAlive = False

            elif honggData == "":
                logging.info("Hongfuzz quit, exiting too\n")
                break
            else:
                # This should not happen
                logging.error( "--[ Unknown Honggfuzz msg: " + str(honggData))


    def _connectAndSendData(self, networkManager, data):
        """
        Connect to server via networkManager and send the data.

        Try several times to create the connection. Returns true if it was
        able to send the data.
        """
        n = 0
        while not networkManager.openConnection():
            n += 1
            if n > 6:
                networkManager.closeConnection()
                return False

        self._sendData(networkManager, data)
        networkManager.closeConnection()

        return True


    def _uploadStats(self):
        """Send fuzzing statistics to parent."""
        currTime = time.time()

        if currTime > self.iterStats["lastUpdate"] + 3:
            fuzzPerSec = float(self.iterStats["iterCount"]) / float(currTime - self.iterStats["startTime"])

            # send fuzzing information to parent process
            d = (self.threadId,
                 self.iterStats["iterCount"],
                 self.iterStats["corpusCount"],
                 self.corpusManager.getCorpusCount(),
                 self.iterStats["crashCount"],
                 self.iterStats["timeoutCount"],
                 fuzzPerSec)
            self.queue.put( d )
            self.iterStats["lastUpdate"] = currTime

            if "nofork" in self.config and self.config["nofork"]:
                print(" %5d: %11d  %9d  %13d  %7d  %4.2f" % d)


    def _prepareHonggfuzzArgs(self):
        """Add all necessary honggfuzz arguments."""
        logging.debug( "Starting server/honggfuzz")
        cmdArr = [ ]

        cmdArr.append(self.config["honggpath"])  # we start honggfuzz
        cmdArr.append('--keep_output')  # keep children output (in log)
        cmdArr.append('--sanitizers')
        cmdArr.append('--sancov')  # Sanitizer coverage feedback, default in honggfuzz 1.2
        cmdArr.append('--threads')  # only one thread
        cmdArr.append('1')
        cmdArr.append('--stdin_input')
        cmdArr.append('--socket_fuzzer')

        # disable LeakAnalyzer because it makes honggfuzz crash
        # https://github.com/dobin/ffw/issues/20
        cmdArr.append('--san_opts')
        cmdArr.append('detect_leaks=0')

        if self.config["debug"]:
            # enable debug mode with log to file
            cmdArr.append("-d")
            cmdArr.append('-l')
            cmdArr.append('honggfuzz.log')

        # only append honggmode specific option if available
        if self.config["honggmode_option"]:
            cmdArr.append(self.config["honggmode_option"])

        # add target to start
        cmdArr.append("--")

        return cmdArr


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
        # update stats
        fuzzingIterationData.getParentCorpus().statsAddCrash()

        srvCrashData = {
            'asanOutput': 'empty',
            'signum': 0,
            'exitcode': 0,
            'reallydead': 0,
            'serverpid': 0,
        }
        crashData = FuzzingCrashData(srvCrashData)
        crashData.setFuzzerPos("-")
        crashinfo.exportFuzzResult(crashData, fuzzingIterationData, self.config)
