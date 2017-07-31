# FFW - Fuzzing For Worms
# Author: Dobin Rutishauser
#
# Based on: 
#   Framework for fuzzing things
#   author: Chris Bisnett

import sys
import os
import subprocess
import time
import shutil
import shlex
import signal 
import sys
import glob

from multiprocessing import Process, Queue

import replay
import bin_crashes
import gui
import network
import interceptor
import ffwchild

def printConfig(config):
    print "Config:  " 
    print "  Running fuzzer:   ", config["fuzzer"]
    print "  Outcomde dir:     ", config["outcome_dir"]
    print "  Target:           ", config["target_bin"]
    print "  Input dir:        ", config["inputs"]
    print "  Analyze response: ", config["response_analysis"]
    

# Fuzzing main parent
#   this is the main entry point for project fuzzers
#   receives data from fuzzing-children via queues
def doFuzz(config, useCurses):
    q = Queue()
    # have to remove sigint handler before forking children
    # so ctlr-c works
    orig = signal.signal(signal.SIGINT, signal.SIG_IGN)

    printConfig(config)

    procs = []
    n = 0
    while n < config["processes"]:
        print "Start child: " + str(n)
        p = Process(target=ffwchild.doActualFuzz, args=(config, n, q))
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
        print "init: " + str(n)
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
    while True: 
        try: 
            r = q.get()
            print "%d: %4d  %8d  %5d" % r
        except KeyboardInterrupt:
            # handle ctrl-c
            for p in procs: 
                p.terminate()
                p.join()

            break

    print("Finished")


def realMain(config):
    func = "fuzz"
    if len(sys.argv) > 1:
        func = sys.argv[1]

    if func == "corpus_destillation":
        corpus_destillation()

    if func == "minimize":
        bin_crashes.minimize(config)

    if func == "replay":
        replay.replay(config, sys.argv[2], sys.argv[3])

    if func == "replayall":
        replay.replayall(config, sys.argv[2])

    if func == "interceptor":
        interceptor.doIntercept(config, sys.argv[2])

    if func == "fuzz":
        useCurses = False
        if len(sys.argv) == 3 and sys.argv[2] == "curses":
            useCurses = True

        doFuzz(config, useCurses)


def corpus_destillation():
    print "Corpus destillation"

