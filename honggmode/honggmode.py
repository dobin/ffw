#!/usr/bin/env python2

import signal
import random
import logging
import os
from multiprocessing import Process, Queue

import time
from . import honggslave


def doFuzz(config):
    """
    Honggmode Fuzzing main parent.

    this is the main entry point for project fuzzers
    receives data from fuzzing-children via queues
    """
    q = Queue()
    # have to remove sigint handler before forking children
    # so ctlr-c works
    orig = signal.signal(signal.SIGINT, signal.SIG_IGN)

    logging.basicConfig(level=logging.ERROR)
    procs = []
    n = 0

    if not _honggExists(config):
        return

    if "nofork" in config and config["nofork"]:
        r = random.randint(0, 2**32 - 1)
        fuzzingSlave = honggslave.HonggSlave(config, n, q, r)
        fuzzingSlave.doActualFuzz()
    else:
        while n < config["processes"]:
            print("Start fuzzing child #" + str(n))
            r = random.randint(0, 2**32 - 1)
            fuzzingSlave = honggslave.HonggSlave(config, n, q, r)
            p = Process(target=fuzzingSlave.doActualFuzz, args=())
            procs.append(p)
            p.start()
            n += 1

    # restore signal handler
    signal.signal(signal.SIGINT, orig)

    fuzzConsole(config, q, procs)


def fuzzConsole(config, q, procs):
    time.sleep(1)
    print("Thread:  Iterations  CorpusNew  CorpusOverall  Crashes  Fuzz/s")
    perf = {}
    while True:
        try:
            r = q.get()
            perf[r[0]] = r
            print(" %5d: %11d  %9d  %13d  %7d  %4.2f" % r)
            #logging.info("%d: %4d  %8d  %5d" % r)
        except KeyboardInterrupt:
            # handle ctrl-c
            for p in procs:
                p.terminate()
                p.join()

            break

    print("Finished")


def _honggExists(config):
    if "honggpath" not in config or config["honggpath"] == "":
        logging.error("Honggfuzz not configured")
        return False

    if not os.path.isfile(config["honggpath"]):
        logging.error("Invalid path to honggfuzz: " + config["honggpath"])
        return False

    return True
