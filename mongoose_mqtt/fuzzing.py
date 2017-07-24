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

    "temp_dir": PROJDIR + "temp",

    "outcome_dir" : PROJDIR + "out",
    "fuzzer": "Radamsa",

    # Path to target
    "target_bin" : PROJDIR + "bin/mqtt_broker",
    "target_args": "%(port)i", # not yet used

    # Directory of input files
    "inputs_raw": PROJDIR + "in_raw",
    "inputs" : PROJDIR + "in",

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
    # can also be manually started
    "corpus_destillation": False,

    # TODO
    # e.g. boofuzz
    "additional_fuzzer": False,

    "sendInitialDataFunction": sendInitialData,
}


def corpus_destillation():
    print "Corpus destillation"

def crash_minimize():
    print "Crash minimize"


def main():
    func = ""

    if func == "corpus_destillation":
        corpus_destillation()

    if func == "crash_minimize":
        crash_minimize()

    try:
        framework.doFuzz(config)
        # bin_crashes.bin_crashes(config)
    except KeyboardInterrupt as e:
        return 0

    return -1

if __name__ == '__main__':
    sys.exit(main())

