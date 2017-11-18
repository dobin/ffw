# FFW - Fuzzing For Worms
# Author: Dobin Rutishauser
#
# Parts of it based on:
#   Framework for fuzzing things
#   author: Chris Bisnett

import logging
import sys
import argparse
import os

from network import replay
from network import interceptor
from fuzzer import fuzzingmaster
from verifier import verifier
from verifier import minimizer
from uploader import uploader
from network import tester
from network import proto_vnc
from honggmode import honggmode


def realMain(config):
    parser = argparse.ArgumentParser("Fuzzing For Worms")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--intercept', help='Intercept and record network communication', action="store_true")
    group.add_argument('--test', help='Test intercepted network communication', action="store_true")
    group.add_argument('--fuzz', help='Perform fuzzing', action="store_true")
    group.add_argument('--honggmode', help='Perform honggfuze based fuzzing', action="store_true")
    group.add_argument('--verify', help='Verify crashes', action="store_true")
    group.add_argument('--minimize', help='Minimize crashes', action="store_true")
    group.add_argument('--replay', help='Replay a crash', action="store_true")
    group.add_argument('--upload', help='Upload verified crashes', action="store_true")

    parser.add_argument('--debug', help="More error messages, only one process", action="store_true")
    parser.add_argument('--gui', help='Fuzzer: Use ncurses gui', action="store_true")
    parser.add_argument('--processes', help='Fuzzer: How many paralell processes', type=int)

    # TODO: make this mode specific
    parser.add_argument("--honggcov", help="Select Honggfuzz coverage", default="sw")
    parser.add_argument('--port', help='Intercept/Replay: Port to be used for the target server', type=int)
    parser.add_argument('--file', help="Verify/Replay: Specify file to be used")
    parser.add_argument('--url', help="Uploader: url")
    parser.add_argument('--basic_auth_user', help='Uploader: basic auth user')
    parser.add_argument('--basic_auth_password', help='Uploader: basic auth password')
    args = parser.parse_args()

    # TODO remove this from here
    if config["proto"] == "vnc":
        print("Using protocol: vnc")
        config["protoObj"] = proto_vnc.ProtoVnc()
    else:
        config["protoObj"] = None

    if args.processes:
        config["processes"] = args.processes

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        config["processes"] = 1
        config["debug"] = True
    else:
        config["debug"] = False

    if args.intercept:
        if args.port:
            interceptor.doIntercept(config, args.port)
        else:
            print "Specify a port with --port"

    if args.test:
        t = tester.Tester(config)
        t.test()

    if args.fuzz:
        fuzzingmaster.doFuzz(config, args.gui)

    if args.honggmode:
        if args.honggcov == "hw" or config["honggcov"] == "hw":
            config["honggmode_option"] = "--linux_perf_bts_edge "

            if os.geteuid() != 0:
                logging.error("--honggcov hw hardware coverage requires root")
                return
        elif args.honggcov == "sw" or config["honggcov"] == "sw":
            config["honggmode_option"] = ""

        honggmode.doFuzz(config)

    if args.verify:
        v = verifier.Verifier(config)

        if args.file:
            v.verifyFile(args.file)
        else:
            v.verifyOutDir()

    if args.minimize:
        mini = minimizer.Minimizer(config)
        mini.minimizeOutDir()

    if args.replay:
        replayer = replay.Replayer(config)

        if not args.file:
            print "Use --file to specify a file to be replayed"
        elif not args.port:
            print "Use --port to specify port to listen on"
        else:
            replayer.replayFile(args.port, args.file)

    if args.upload:
        if args.basic_auth_user and args.basic_auth_password:
            u = uploader.Uploader(config, args.url, args.basic_auth_user, args.basic_auth_password)
        else:
            u = uploader.Uploader(config, args.url, None, None)

        u.uploadVerifyDir()


def realMain2(config):
    func = "fuzz"

    if config["debug"]:
        print("Debug mode enabled")
        logging.basicConfig(level=logging.DEBUG)
        config["processes"] = 1

    if config["proto"] == "vnc":
        print("Using protocol: vnc")
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

    if func == "honggmode":
        honggmode.doFuzz(config)
