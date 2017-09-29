#!/usr/bin/env python2

import pickle
import os
import logging
import sys


def readPickleFile(fileName):
    data = None

    with open(fileName, 'rb') as f:
        data = pickle.load(f)

    return data


def prepareInput(config):
    file = config["inputs"] + "/data_0.pickle"

    if not os.path.isfile(file):
        logging.error("Could not read input file: " + file)
        sys.exit(0)

    with open(file, 'rb') as f:
        config["_inputs"] = pickle.load(f)

    n = 0
    for input in config["_inputs"]:
        input["index"] = n
        #print "A: " + str(input)
        n += 1

    #print config["_inputs"]
