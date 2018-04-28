#!/usr/bin/env python2

import random
import logging
import os
import subprocess
import copy
import time
import sys
import glob

from mutator_list import mutators
import utils


def testMutatorConfig(config):
    """
    Test if config for mutator is ok.

    This is not being used for mutator related unit tests.
    """
    if not config["mutator"] in mutators:
        logging.error("Could not find fuzzer with name: " + self.config["fuzzer"])
        return False
    fuzzerData = mutators[ config["mutator"] ]

    fuzzerBin = config["basedir"] + "/" + fuzzerData["file"]
    if not os.path.isfile(fuzzerBin):
        logging.error("Could not find fuzzer binary: " + fuzzerBin)
        return False

    return True


class MutatorInterface(object):
    def __init__(self, config):
        self.config = config
        self.seed = None
        self._loadConfig()


    def _loadConfig(self):
        # checked in testMutatorConfig
        self.fuzzerData = mutators[ self.config["mutator"] ]

        # checked in testMutatorConfig
        self.fuzzerBin = self.config["basedir"] + "/" + self.fuzzerData["file"]

        # not checked atm
        self.grammars_string = ""
        if "grammars" in self.config:
            for root, dirs, files in os.walk(self.config["grammars"]):
                for element in files:
                    self.grammars_string += self.config["grammars"] + element + " "

        # check generative fuzzer
        if self.fuzzerData["type"] is not "mut":
            logging.debug("Not loading any data, as generative fuzzer")
            # create fake data.
            # TODO


    def _generateSeed(self):
        self.seed = str(random.randint(0, 2**64 - 1))


    def fuzz(self, corpusData):
        logging.debug("Fuzz the data")

        self._generateSeed()

        self.fuzzingInFile = os.path.join(
            self.config["temp_dir"],
            str(self.seed) + ".in.raw")
        self.fuzzingOutFile = os.path.join(
            self.config["temp_dir"],
            str(self.seed) + ".out.raw")

        corpusDataNew = corpusData.createFuzzChild(self.seed)
        initialData = corpusDataNew.networkData.getFuzzMessageData()

        self._writeDataToFile(initialData)
        self._runFuzzer()
        fuzzedData = self._readDataFromFile()
        corpusDataNew.networkData.setFuzzMessageData(fuzzedData)

        return corpusDataNew


    def _writeDataToFile(self, data):
        """Write the data to be mutated to a file."""
        file = open(self.fuzzingInFile, "w")
        file.write(data)
        file.close()


    def _readDataFromFile(self):
        """
        Read the mutated data.

        The fuzzer has generated a new file with fuzzed data.
        Read it, then remove that file.
        Also remove the original input file.
        """
        file = open(self.fuzzingOutFile, "r")
        data = file.read()
        file.close()

        logging.debug("Read fuzzing data: " + utils.cap(data, 64))

        try:
            os.remove(self.fuzzingInFile)
        except:
            logging.warn("Failed to remove file %s!" % self.fuzzingInFile)

        # keep fuzzed files for debugging purposes
        if "keep_temp" in self.config and self.config["keep_temp"]:
            pass
        else:
            try:
                os.remove(self.fuzzingOutFile)
            except:
                logging.warn("Failed to remove file %s!" % self.fuzzingOutFile)

        return data


    def _runFuzzer(self):
        """Call external fuzzer"""
        logging.info("Call mutator, seed: " + str(self.seed))

        args = self.fuzzerData["args"] % ({
            "seed": self.seed,
            "grammar": self.grammars_string,
            "input": self.fuzzingInFile,
            "output": self.fuzzingOutFile})

        logging.debug("Mutator command args: " + args)
        subprocess.call(self.fuzzerBin + " " + args, shell=True)

        return True
