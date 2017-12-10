#!/usr/bin/env python2

import pickle
import os
import logging
import sys
import glob

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


def loadInputs(config):
    inputs = []

    inputFiles = glob.glob(os.path.join(config["inputs"], '*'))
    for inputFile in inputFiles:
        try:
            with open(inputFile, 'rb') as f:
                data = pickle.load(f)
                fixMsgs(data)
                inputs.append(data)
        except:
            #logging.error("E: " + str(e))
            pass



    print("Loaded " + str(len(inputs)) + " inputs")

    return inputs
