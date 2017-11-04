#!/usr/bin/env python2

import signal
import random
import logging

from multiprocessing import Process, Queue

import utils
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

    utils.prepareInput(config)

    procs = []
    n = 0

    while n < config["processes"]:
        print("Start child: " + str(n))
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
    while True:
        try:
            r = q.get()
            print("%d: %4d  %8d  %5d" % r)
            logging.info("%d: %4d  %8d  %5d" % r)
        except KeyboardInterrupt:
            # handle ctrl-c
            for p in procs:
                p.terminate()
                p.join()

            break

    print("Finished")
