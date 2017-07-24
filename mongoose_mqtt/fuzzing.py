#!/usr/bin/python
#
# Basic fuzzing handler
#
# @author Chris Bisnett

import sys
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

import framework

BASEDIR = "/home/vagrant/ffw/"
PROJDIR = BASEDIR + "mongoose_mqtt/"

CONFIG = {
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

    # check code coverage?
    "gcov_coverage": False,
    "gcov_coverage_time": 10000, # in iterations

    # crash analysis?
    "crash_minimize": False, 
    "crash_minimize_time": 3, # number of new crashes
}

def main():
    try:
        framework.doFuzz(CONFIG)
    except KeyboardInterrupt as e:
        return 0

    return -1

if __name__ == '__main__':
    sys.exit(main())

