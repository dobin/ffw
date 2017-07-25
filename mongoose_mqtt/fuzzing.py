#!/usr/bin/python
#
# Based on: 
#   Framework for fuzzing things
#   author: Chris Bisnett

import sys
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

import framework
import bin_crashes

BASEDIR = "/home/vagrant/ffw/"
PROJDIR = BASEDIR + "mongoose_mqtt/"


def sendInitialData(socket):
    authData = "\x10\x16\x00\x04\x4d\x51\x54\x54\x04\x02\x00\x00\x00\x0a\x6d\x79\x63\x6c\x69\x65\x6e\x74\x69\x64"
    socket.sendall(authData)


config = {
    "basedir": BASEDIR,
    "projdir": PROJDIR,

    # fuzzed files are generated here
    "temp_dir": PROJDIR + "temp",

    # where are input which crash stuff stored
    "outcome_dir" : PROJDIR + "out",

    # which fuzzer should be used
    "fuzzer": "Radamsa",

    # Path to target
    "target_bin" : PROJDIR + "bin/mqtt_broker",
    "target_args": "%(port)i", # not yet used TODO

    # Directory of input files
    "inputs_raw": PROJDIR + "in_raw", # TODO not yet used
    "inputs" : PROJDIR + "in",

    # if you have multiple ffw fuzzers active,
    # change this between them
    "baseport": 30000,

    # analyze response for information leak? (slow)
    "response_analysis": False,

    # TODO
    # check code coverage?
    "gcov_coverage": False,
    "gcov_coverage_time": 10000, # in iterations

    # TODO
    # crash analysis?
    "crash_minimize": False, 
    "crash_minimize_time": 3, # number of new crashes

    # TODO
    # Note: can also be manually started
    "corpus_destillation": False,

    # TODO
    # e.g. boofuzz
    "additional_fuzzer": False,

    # send data before the actual fuzzing packet
    # e.g. authentication
    #"sendInitialDataFunction": sendInitialData,
    "sendInitialDataFunction": None,

    # how many fuzzing instances should we start
    # Note: server needs to support port on command line
    # for this feature to work
    "processes": 3,
}


def corpus_destillation():
    print "Corpus destillation"


def main():
    func = "fuzz"
    if len(sys.argv) == 2:
        func = sys.argv[1]
    

    if func == "corpus_destillation":
        corpus_destillation()

    if func == "minimize":
        bin_crashes.minimize(config)

    if func == "fuzz":
        try:
            framework.doFuzz(config)
        except KeyboardInterrupt as e:
            return 0

#    return -1

if __name__ == '__main__':
    sys.exit(main())

