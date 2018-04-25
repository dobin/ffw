#!/usr/bin/env python2

import signal
import random

from multiprocessing import Process, Queue

from . import clientfuzzerslave
import utils


def doFuzz(config, useCurses):
    """
    Client Fuzzing main parent.

    this is the main entry point for project fuzzers
    receives data from fuzzing-children via queues
    """
    q = Queue()
    # have to remove sigint handler before forking children
    # so ctlr-c works
    orig = signal.signal(signal.SIGINT, signal.SIG_IGN)

    inputs = utils.loadInputs(config)

    procs = []
    n = 0

    if "fuzzer_nofork" in config and config["fuzzer_nofork"]:
        r = random.randint(0, 2**32 - 1)
        fuzzingSlave = clientfuzzerslave.FuzzingSlave(config, n, q, r)
        fuzzingSlave.doActualFuzz()
    else:
        while n < config["processes"]:
            print("Start child: " + str(n))
            r = random.randint(0, 2**32 - 1)
            fuzzingSlave = clientfuzzerslave.FuzzingSlave(config, n, q, r, inputs)
            p = Process(target=fuzzingSlave.doActualFuzz, args=())
            procs.append(p)
            p.start()
            n += 1

    # restore signal handler
    signal.signal(signal.SIGINT, orig)

    print("Thread#  Fuzz/s   Count   Crashes")
    while True:
        try:
            r = q.get()
            print("%d: %4.2f  %8d  %5d" % r)
        except KeyboardInterrupt:
            # handle ctrl-c
            for p in procs:
                p.terminate()
                p.join()

            break

    print("Finished")
