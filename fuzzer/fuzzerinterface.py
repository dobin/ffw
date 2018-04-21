#!/usr/bin/env python2

import random
import logging
import os
import subprocess
import copy
import time
import sys

from fuzzer_list import fuzzers
import utils


class FuzzerInterface(object):

    def __init__(self, config):
        self.config = config
        self.seed = None

    def _generateSeed(self):
        self.seed = random.randint(0, 2**64 - 1)


    def fuzz(self, corpusData):
        """
        Creates self.fuzzedData.

        By selecting a message, and mutate it by calling a fuzzer
        returns False if something went wrong
        """
        logging.debug("Fuzzing the data")

        self._generateSeed()

        self.fuzzingInFile = os.path.join(
            self.config["temp_dir"],
            str(self.seed) + ".in.raw")
        self.fuzzingOutFile = os.path.join(
            self.config["temp_dir"],
            str(self.seed) + ".out.raw")

        logging.debug("Fuzzing the data1")
        corpusDataNew = copy.deepcopy(corpusData)
        corpusDataNew.seed = self.seed
        corpusDataNew.networkData.selectMessage()
        logging.debug("Fuzzing the data2")
        initialData = corpusDataNew.networkData.getFuzzMessageData()

        logging.debug("Fuzzing the data3")
        self._writeDataToFile(initialData)
        self._runFuzzer()
        fuzzedData = self._readDataFromFile()
        logging.debug("Fuzzing the data4")
        corpusDataNew.networkData.setFuzzMessageData(fuzzedData)
        return corpusDataNew


    def _writeDataToFile(self, data):
        """Write the data to be fuzzed to a file."""
        file = open(self.fuzzingInFile, "w")
        file.write(data)
        file.close()


    def _readDataFromFile(self):
        """
        Read the fuzzed data

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
            print("Failed to remove file %s!" % self.fuzzingInFile)

        # keep fuzzed files for debugging purposes
        if "keep_temp" in self.config and self.config["keep_temp"]:
            pass
        else:
            try:
                os.remove(self.fuzzingOutFile)
            except:
                print("Failed to remove file %s!" % self.fuzzingOutFile)

        return data


    def _runFuzzer(self):
        """Call external fuzzer"""
        logging.info("Call fuzzer, seed: " + str(self.seed))

        fuzzerData = fuzzers[ self.config["fuzzer"] ]
        if not fuzzerData:
            print("Could not find fuzzer with name: " + self.config["fuzzer"])
            return False

        fuzzerBin = self.config["basedir"] + "/" + fuzzerData["file"]
        if not os.path.isfile(fuzzerBin):
            print("Could not find fuzzer binary: " + fuzzerBin)
            sys.exit()

        grammars_string = ""
        if "grammars" in self.config:
            for root, dirs, files in os.walk(self.config["grammars"]):
                for element in files:
                    grammars_string += self.config["grammars"] + element + " "

        args = fuzzerData["args"] % ({
            "seed": self.seed,
            "grammar": grammars_string,
            "input": self.fuzzingInFile,
            "output": self.fuzzingOutFile})
        logging.debug("CMD: " + args)
        subprocess.call(fuzzerBin + " " + args, shell=True)

        return True
