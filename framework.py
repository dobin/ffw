# FFW - Fuzzing For Worms
# Author: Dobin Rutishauser
#
# Based on:
#   Framework for fuzzing things
#   author: Chris Bisnett

import logging
import sys

from network import replay
from network import interceptor
from fuzzer import fuzzingmaster
from verifier import verifier
from verifier import minimizer
from uploader import uploader
from network import tester
from network import proto_vnc


def realMain(config):
    func = "fuzz"

    if config["debug"]:
        print "Debug mode enabled"
        logging.basicConfig(level=logging.DEBUG)
        config["processes"] = 1

    if config["proto"] == "vnc":
        print "Using protocol: vnc"
        config["protoObj"] = proto_vnc.ProtoVnc()
    else:
        config["protoObj"] = None

    if len(sys.argv) > 1:
        func = sys.argv[1]

    #if func == "corpus_destillation":
        #corpus_destillation()

    if func == "upload":
        if len(sys.argv) == 5:
            u = uploader.Uploader(config, sys.argv[2], sys.argv[3], sys.argv[4])
        else:
            u = uploader.Uploader(config, sys.argv[2], None, None)
        u.uploadVerifyDir()

    if func == "test":
        t = tester.Tester(config)
        t.test()

    if func == "verify":
        v = verifier.Verifier(config)
        if len(sys.argv) == 2:
            v.verifyOutDir()
        else:
            v.verifyFile(sys.argv[2])


    if func == "minimize":
        mini = minimizer.Minimizer(config)
        mini.minimizeOutDir()

    if func == "replay":
        replayer = replay.Replayer(config)
        replayer.replayFile(sys.argv[2], sys.argv[3])

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
