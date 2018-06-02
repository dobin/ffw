#!/usr/bin/env python2

import sys
import signal
import random
import logging
import os
from multiprocessing import Process, Queue
from Queue import Empty
import time
import threading
from enum import Enum

from honggcorpusmanager import HonggCorpusManager
from . import honggslave
from honggstats import HonggStats


class FuzzerState(Enum):
    START = 1
    WARMUP = 2
    FUZZING = 3


class HonggMaster(object):
    def __init__(self, config):
        self.honggStats = None
        self.config = config
        self.fuzzerState = FuzzerState.START
        self.nextUpdateTime = None


    def doFuzz(self):
        """
        Honggmode Fuzzing main parent.

        this is the main entry point for project fuzzers
        receives data from fuzzing-children via queues
        """
        q = Queue()

        logging.basicConfig(level=logging.ERROR)

        if not self._honggExists():
            return

        # this corpusManager is only to test if we have input files
        corpusManager = HonggCorpusManager(self.config)
        corpusManager.loadCorpusFiles()
        if corpusManager.getCorpusCount() == 0:
            logging.error("No corpus input data found in: " + self.config['input_dir'])
            return

        # special mode, will not fork
        if "fuzzer_nofork" in self.config and self.config["fuzzer_nofork"]:
            self._fuzzNoFork(q)
        else:
            self._fuzzWithFork(q)


    def _fuzzWithFork(self, q):
        # have to remove sigint handler before forking children
        # so ctlr-c works
        orig = signal.signal(signal.SIGINT, signal.SIG_IGN)

        procs = []
        n = 0

        # prepare data structure
        while n < self.config["processes"]:
            print("Start fuzzing child #" + str(n))
            r = random.randint(0, 2**32 - 1)

            proc = {
                "r": r,
                "q": q,
                "config": self.config,
                "n": n,
                "p": None,
            }
            procs.append(proc)
            n += 1

        # start processes
        for proc in procs:
            self._startThread(proc)

        self.state = FuzzerState.WARMUP

        # restore signal handler
        signal.signal(signal.SIGINT, orig)

        self._fuzzConsole(q, procs)


    def _startThread(self, proc):
        fuzzingSlave = honggslave.HonggSlave(
            proc["config"],
            proc["n"],
            proc["q"],
            proc["r"])
        p = Process(target=fuzzingSlave.doActualFuzz, args=())
        p.start()
        self.state = FuzzerState.WARMUP
        proc["p"] = p


    def _fuzzNoFork(self, q):
        r = random.randint(0, 2**32 - 1)
        fuzzingSlave = honggslave.HonggSlave(self.config, 0, q, r)
        self.state = FuzzerState.FUZZING
        fuzzingSlave.doActualFuzz()


    def _fuzzConsole(self, q, procs):
        honggStats = HonggStats(len(procs))
        self.honggStats = honggStats
        honggStats.start()

        n = 0
        while True:
            # wait for new data from threads
            try:
                try:
                    r = q.get(True, 1)
                    self.fuzzerState = FuzzerState.FUZZING
                    self._startPeriodicThreads()
                    honggStats.addToStats(r)
                    # self._printThreadStats(r)
                except Empty:
                    pass

            except KeyboardInterrupt:
                honggStats.writeFuzzerStats()
                honggStats.finish()

                # handle ctrl-c
                for proc in procs:
                    proc["p"].terminate()
                    proc["p"].join()

                break

            # check regularly if process crashed/exited - if yes, restart it
            # This may occur if honggfuzz crashed
            # Do not restart in debug mode
            if "debug" not in self.config:
                for proc in procs:
                    if proc["p"].exitcode is not None or not proc["p"].is_alive():
                        logging.warn("Honggfuzz (and with it the target) crashed. Restarting.")
                        logging.warn("If this is happening often, fuzz with --debug and check")
                        logging.warn("bin/honggfuzz.log and bin/*.fuzz and bin/HONGGFUZZ.REPORT.TXT")
                        self._startThread(proc)

            n += 1
        print("Finished")


    def _startPeriodicThreads(self):
        if self.nextUpdateTime is None:
            self.nextUpdateTime = time.time() + 10

        if time.time() > self.nextUpdateTime:
            self.nextUpdateTime = time.time() + 10
            self._periodicWriteData()
            self._periodicSanityChecks()
            self._periodicPrintStats()


    def _periodicPrintStats(self):
        if self.fuzzerState is FuzzerState.FUZZING:
            self.honggStats.printSomeStats()


    def _periodicWriteData(self):
        if self.fuzzerState is FuzzerState.FUZZING:
            self.honggStats.writePlotData()
            self.honggStats.writeFuzzerStats()


    def _periodicSanityChecks(self):
        if self.fuzzerState is FuzzerState.FUZZING:
            self.honggStats.sanityChecks()


    def _honggExists(self):
        if "honggpath" not in self.config or self.config["honggpath"] == "":
            logging.error('Honggfuzz not configured. Require path to honggfuzz in config in "honggpath".')
            return False

        if not os.path.isfile(self.config["honggpath"]):
            logging.error('Invalid path to honggfuzz in config["honggpath"]: ' + self.config["honggpath"])
            return False

        return True
