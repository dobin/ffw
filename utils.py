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


def setupSlaveLoggingWithFile(threadId):
    f = 'ffw-debug-slave-' + str(threadId) + '.log'

    fileh = logging.FileHandler(f, 'a')
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    fileh.setFormatter(formatter)

    log = logging.getLogger()  # root logger
    for hdlr in log.handlers[:]:  # remove all old handlers
        log.removeHandler(hdlr)
    log.addHandler(fileh)      # set the new handler

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.WARN)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
