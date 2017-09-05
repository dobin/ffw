# FFW - Fuzzing For Worms
# Author: Dobin Rutishauser
#
# Based on:
#   Framework for fuzzing things
#   author: Chris Bisnett

import logging
import sys

import replay
import minimizer
import gui
import interceptor
import fuzzingmaster

def realMain(config):
    func = "fuzz"

    if config["debug"]:
        print "Debug mode enabled"
        logging.basicConfig(level=logging.DEBUG)
        config["processes"] = 2


    if len(sys.argv) > 1:
        func = sys.argv[1]

    #if func == "corpus_destillation":
        #corpus_destillation()

    if func == "minimize":
        mini = minimizer.Minimizer(config)
        mini.minimizeOutDir()

    if func == "replay":
        replay.replayFile(sys.argv[2], sys.argv[3])

    if func == "replayall":
        replay.replayAllFiles(config, sys.argv[2])

    if func == "interceptor":
        interceptor.doIntercept(config, sys.argv[2])

    if func == "interceptorreplay":
        interceptor.replayAll(config)

    if func == "fuzz":
        useCurses = False
        if len(sys.argv) == 3 and sys.argv[2] == "curses":
            useCurses = True

        fuzzingmaster.doFuzz(config, useCurses)
