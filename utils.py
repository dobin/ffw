#!/usr/bin/env python2

import pickle
import os
import logging
import sys

"""
Several utility functions.

Mostly related to reading pickle files.
Shared by different phases of the framework.
"""


def readPickleFile(fileName):
    data = None

    with open(fileName, 'rb') as f:
        data = pickle.load(f)

    return data


def fixMsgs(messages):
    n = 0
    for msg in messages:
        msg["index"] = n
        n += 1


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
        n += 1
