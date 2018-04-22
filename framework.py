# FFW - Fuzzing For Worms
# Author: Dobin Rutishauser

import logging
import argparse
import os
import glob

from network import replay
from network.interceptor import Interceptor
from fuzzer import fuzzer_list
from clientfuzzer import clientfuzzermaster
from verifier import verifier
from verifier import minimizer
from uploader import uploader
from network import tester
from network import proto_vnc

from basicmode import basicmaster
from honggmode import honggmaster
import distutils.spawn


def checkRequirements(config):
    if not os.path.isfile(config["target_bin"]):
        print "Target binary not found: " + str(config["target_bin"])
        return False

    if not os.path.isdir(config["temp_dir"]):
        print "Temp directory not found: " + str(config["temp_dir"])
        return False

    if distutils.spawn.find_executable("gdb") is None:
        print "GDB not installed?"
        return False

    return True


def checkFuzzRequirements(config):
    if fuzzer_list.fuzzers[config["fuzzer"]]["type"] == "gen":
        return True

    f = config["projdir"] + '/in/*.pickle'
    if len( glob.glob(f)) <= 0:
        print "No intercepted data found: " + str(f)
        return False

    return True


# https://stackoverflow.com/questions/9321741/printing-to-screen-and-writing-to-a-file-at-the-same-time
def setupLoggingWithFile(config):
    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='ffw-debug.log',
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.WARN)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    # slaves will setup their own logging
    config["DebugWithFile"] = True


def setupLoggingStandard():
    logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')


def loadConfig(configfilename, basedir):
    rawData = open(configfilename, 'r').read()

    # hmm this produces some strange behaviour upon string comparison
    # of the values of the dict
    #pyData = ast.literal_eval(rawData)
    pyData = eval(rawData)

    pyData["basedir"] = basedir
    pyData["projdir"] = os.getcwd() + "/"

    # cleanup. Damn this is ugly.
    pyData["target_bin"] = pyData["projdir"] + pyData["target_bin"]
    pyData["temp_dir"] = pyData["projdir"] + pyData["temp_dir"]
    pyData["outcome_dir"] = pyData["projdir"] + pyData["outcome_dir"]
    pyData["grammars"] = pyData["projdir"] + pyData["grammars"]
    pyData["inputs"] = pyData["projdir"] + pyData["inputs"]
    pyData["verified_dir"] = pyData["projdir"] + pyData["verified_dir"]

    return pyData


def realMain(config):
    parser = argparse.ArgumentParser("Fuzzing For Worms")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--intercept', help='Intercept and record network communication', action="store_true")
    group.add_argument('--test', help='Test intercepted network communication', action="store_true")
    group.add_argument('--fuzz', help='Perform fuzzing', action="store_true")
    group.add_argument('--clientfuzz', help='Perform client fuzzing', action="store_true")
    group.add_argument('--honggmode', help='Perform honggfuze based fuzzing', action="store_true")
    group.add_argument('--verify', help='Verify crashes', action="store_true")
    group.add_argument('--minimize', help='Minimize crashes', action="store_true")
    group.add_argument('--replay', help='Replay a crash', action="store_true")
    group.add_argument('--upload', help='Upload verified crashes', action="store_true")

    parser.add_argument('--debug', help="More error messages, only one process", action="store_true")
    parser.add_argument('--gui', help='Fuzzer: Use ncurses gui', action="store_true")
    parser.add_argument('--processes', help='Fuzzer: How many paralell processes', type=int)

    # TODO: make this mode specific
    parser.add_argument("--honggcov", help="Select Honggfuzz coverage: hw/sw", default="sw")
    parser.add_argument('--listenport', help='Intercept: Listener port', type=int)
    parser.add_argument('--targetport', help='Intercept/Replay: Port to be used for the target server', type=int)
    parser.add_argument('--file', help="Verify/Replay: Specify file to be used")
    parser.add_argument('--url', help="Uploader: url")
    parser.add_argument('--basic_auth_user', help='Uploader: basic auth user')
    parser.add_argument('--basic_auth_password', help='Uploader: basic auth password')
    parser.add_argument('--adddebuglogfile', help='Will write a debug log file', action="store_true")

    parser.add_argument('--config', help='Config file')
    parser.add_argument('--basedir', help='FFW base directory')
    args = parser.parse_args()

    if config is None:
        if args.config is None:
            print "No config specified. Either start via fuzzing.py, or with --config <configfile>"
            return
        else:
            if not args.basedir:
                print "Please specify FFW basedir"
            else:
                config = loadConfig(args.config, args.basedir)

    if not checkRequirements(config):
        print "Requirements not met."
        return

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

    if args.adddebuglogfile:
        setupLoggingWithFile(config)
    else:
        setupLoggingStandard()

    if args.intercept:
        interceptorPort = 10000
        targetPort = 20000

        if args.listenport:
            interceptorPort = args.listenport

        if args.targetport:
            targetPort = args.targetport
        else:
            targetPort = config["baseport"]

        print("Interceptor listen on port: " + str(interceptorPort))
        print("Target server port: " + str(targetPort))

        interceptor = Interceptor(config)
        interceptor.doIntercept(interceptorPort, targetPort)

    if args.test:
        t = tester.Tester(config)
        t.test()

    if args.fuzz:
        if not checkFuzzRequirements(config):
            return False
        basicmaster.doFuzz(config, args.gui)

    if args.clientfuzz:
        if not checkFuzzRequirements(config):
            return False
        clientfuzzermaster.doFuzz(config, args.gui)

    if args.honggmode:
        if not checkFuzzRequirements(config):
            return False

        if args.honggcov == "hw" or config["honggcov"] == "hw":
            config["honggmode_option"] = "--linux_perf_bts_edge"

            if os.geteuid() != 0:
                logging.error("--honggcov hw hardware coverage requires root")
                return
        elif args.honggcov == "sw" or config["honggcov"] == "sw":
            config["honggmode_option"] = None  # sw is default
        else:
            config["honggmode_option"] = None

        honggmaster.doFuzz(config)

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
        elif not args.targetport:
            print "Use --targetport to specify port to send data to"
        else:
            replayer.replayFile(args.targetport, args.file)

    if args.upload:
        if args.basic_auth_user and args.basic_auth_password:
            u = uploader.Uploader(config, args.url, args.basic_auth_user, args.basic_auth_password)
        else:
            u = uploader.Uploader(config, args.url, None, None)

        u.uploadVerifyDir()
