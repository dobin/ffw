#!/usr/bin/env python2

import signal
import random
import gui
import logging

from multiprocessing import Process, Queue

from . import basicslave
from fuzzer.fuzzer_list import fuzzers
import utils


def doFuzz(config, useCurses):
    """
    Fuzzing main parent.

    this is the main entry point for project fuzzers
    receives data from fuzzing-children via queues
    """
    q = Queue()
    # have to remove sigint handler before forking children
    # so ctlr-c works
    orig = signal.signal(signal.SIGINT, signal.SIG_IGN)

    printConfig(config)
    if fuzzers[config["fuzzer"]]["type"] == "mut":
        logging.debug("Loading recorded data...")
    else:
        logging.debug("Not loading any data, as generative fuzzer")
        # create fake data.
        # an list with: a list of network messages
        inputs = [
            [
                {
                    "data": "",
                    "from": "cli",
                },
                {
                    "data": "",
                    "from": "srv",
                },
            ]
        ]

    procs = []
    n = 0

    if "fuzzer_nofork" in config and config["fuzzer_nofork"]:
        r = random.randint(0, 2**32 - 1)
        basicSlave = basicslave.BasicSlave(config, n, q, r)
        basicSlave.doActualFuzz()
    else:
        while n < config["processes"]:
            print("Start child: " + str(n))
            r = random.randint(0, 2**32 - 1)
            basicSlave = basicslave.BasicSlave(config, n, q, r)
            p = Process(target=basicSlave.doActualFuzz, args=())
            procs.append(p)
            p.start()
            n += 1

    # restore signal handler
    signal.signal(signal.SIGINT, orig)

    if useCurses:
        fuzzCurses(config, q, procs)
    else:
        fuzzConsole(config, q, procs)


def fuzzCurses(config, q, procs):
    data = [None] * config["processes"]
    n = 0
    while n < config["processes"]:
        print("init: " + str(n))
        data[n] = {
            "testspersecond": 0,
            "testcount": 0,
            "crashcount": 0,
        }
        n += 1

    screen, boxes = gui.initGui( config["processes"] )

    while True:
        try:
            r = q.get()
            data[r[0]] = {
                "testspersecond": r[1],
                "testcount": r[2],
                "crashcount": r[3],
            }
            gui.updateGui(screen, boxes, data)
            #print "%d: %4d  %8d  %5d" % r
        except KeyboardInterrupt:
            # handle ctrl-c
            for p in procs:
                p.terminate()
                p.join()

            gui.cleanup()

            break


def fuzzConsole(config, q, procs):
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


def printConfig(config):
    print("Config:  ")
    print("  Running fuzzer:   ", config["fuzzer"])
    print("  Outcomde dir:     ", config["outcome_dir"])
    print("  Target:           ", config["target_bin"])
    print("  Input dir:        ", config["input_dir"])
    print("  Analyze response: ", config["response_analysis"])
