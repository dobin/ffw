#!/usr/bin/env python2

import sys
import signal
import random
import logging
import os
from multiprocessing import Process, Queue
from Queue import Empty

from honggcorpusmanager import HonggCorpusManager
from . import honggslave
from honggstats import HonggStats


def doFuzz(config):
    """
    Honggmode Fuzzing main parent.

    this is the main entry point for project fuzzers
    receives data from fuzzing-children via queues
    """
    q = Queue()

    logging.basicConfig(level=logging.ERROR)

    if not _honggExists(config):
        return

    # this corpusManager is only to test if we have input files
    corpusManager = HonggCorpusManager(config)
    corpusManager.loadCorpusFiles()
    if corpusManager.getCorpusCount() == 0:
        logging.error("No corpus input data found in: " + config['input_dir'])
        return

    # special mode, will not fork
    if "fuzzer_nofork" in config and config["fuzzer_nofork"]:
        _fuzzNoFork(config, q)
    else:
        _fuzzWithFork(config, q)


def _fuzzWithFork(config, q):
    # have to remove sigint handler before forking children
    # so ctlr-c works
    orig = signal.signal(signal.SIGINT, signal.SIG_IGN)

    procs = []
    n = 0

    # prepare data structure
    while n < config["processes"]:
        print("Start fuzzing child #" + str(n))
        r = random.randint(0, 2**32 - 1)

        proc = {
            "r": r,
            "q": q,
            "config": config,
            "n": n,
            "p": None,
        }
        procs.append(proc)
        n += 1

    # start processes
    for proc in procs:
        _startThread(proc)

    # restore signal handler
    signal.signal(signal.SIGINT, orig)

    _fuzzConsole(config, q, procs)


def _startThread(proc):
    fuzzingSlave = honggslave.HonggSlave(
        proc["config"],
        proc["n"],
        proc["q"],
        proc["r"])
    p = Process(target=fuzzingSlave.doActualFuzz, args=())
    p.start()
    proc["p"] = p


def _fuzzNoFork(config, q):
    r = random.randint(0, 2**32 - 1)
    fuzzingSlave = honggslave.HonggSlave(config, 0, q, r)
    fuzzingSlave.doActualFuzz()


def _fuzzConsole(config, q, procs):
    honggStats = HonggStats(len(procs))
    honggStats.start()

    n = 0
    while True:
        if n % 5 == 0:
            honggStats.writePlotData()
            honggStats.writeFuzzerStats()

        if n % 10 == 0:
            honggStats.sanityChecks()

        # wait for new data from threads
        try:
            try:
                r = q.get(True, 1)
                honggStats.addToStats(r)
                print("%3d  It: %4d  CorpusNew: %2d  CorpusOerall %2d  Crashes: %2d  HangCount: %2d  Fuzz/s: %.1f  Latency: %.4f" % r)
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
        if "debug" not in config:
            for proc in procs:
                if proc["p"].exitcode is not None or not proc["p"].is_alive():
                    logging.warn("Honggfuzz (and with it the target) crashed. Restarting.")
                    logging.warn("If this is happening often, fuzz with --debug and check")
                    logging.warn("bin/honggfuzz.log and bin/*.fuzz and bin/HONGGFUZZ.REPORT.TXT")
                    _startThread(proc)

        n += 1
    print("Finished")


def _honggExists(config):
    if "honggpath" not in config or config["honggpath"] == "":
        logging.error('Honggfuzz not configured. Require path to honggfuzz in config in "honggpath".')
        return False

    if not os.path.isfile(config["honggpath"]):
        logging.error('Invalid path to honggfuzz in config["honggpath"]: ' + config["honggpath"])
        return False

    return True
