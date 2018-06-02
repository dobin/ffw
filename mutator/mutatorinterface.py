#!/usr/bin/env python2

import random
import logging
import os
import subprocess
import sys

from mutator_list import mutators
from mutator_dictionary import MutatorDictionary
import utils


def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)


def testMutatorConfig(config, mode):
    """
    Test if config for mutator is ok.

    This is not being used for mutator related unit tests.
    """
    for mutator in config['mutator']:
        # check if binary exists
        if mutator not in mutators:
            logging.error("Could not find fuzzer with name: " + config["mutator"])
            return False
        fuzzerData = mutators[ mutator ]

        # gen cannot be used with hongg
        if fuzzerData['type'] is 'gen' and mode is 'hongg':
            logging.error("Using a generative fuzzer in honggmode is not really possible")
            return False

        # class/file
        if 'class' in fuzzerData:
            if not str_to_class(fuzzerData['class']):
                logging.error("Class does not exist: " + fuzzerData['class'])
        elif 'file' in fuzzerData:
            fuzzerBin = config["basedir"] + "/" + fuzzerData["file"]
            if not os.path.isfile(fuzzerBin):
                logging.error("Could not find fuzzer binary: " + fuzzerBin)
                return False
        else:
            logging.error("Fuzzer is neither file or class")
            return False

    return True


class MutatorInterface(object):
    def __init__(self, config, threadId):
        self.config = config
        self.seed = None
        self.threadId = threadId
        self.fuzzerClassInstances = {}
        self._loadConfig()
        self.currentFuzzerIndex = 0


    def _loadConfig(self):
        for mutator in self.config["mutator"]:
            # checked in testMutatorConfig
            fuzzerData = mutators[ mutator ]

            # checked in testMutatorConfig
            if 'file' in fuzzerData:
                self.fuzzerBin = self.config["basedir"] + "/" + fuzzerData["file"]

            # not checked atm
            self.grammars_string = ""
            if "grammars" in self.config:
                for root, dirs, files in os.walk(self.config["grammars"]):
                    for element in files:
                        self.grammars_string += self.config["grammars"] + element + " "

            # check generative fuzzer
            if fuzzerData["type"] is not "mut":
                logging.debug("Not loading any data, as generative fuzzer")
                # create fake data.
                # TODO


    def _generateSeed(self):
        self.seed = str(random.randint(0, 2**64 - 1))


    def fuzz(self, corpusData):
        logging.debug("Fuzz the data")

        self._generateSeed()

        fuzzedCorpusData = None
        # a fuzzer may have exhausted all possible permutations
        # (which will return None)
        # if that happens, get data from another fuzzer
        # but not forever, only until we tried them all (via n)
        n = 0
        while fuzzedCorpusData is None:
            fuzzerChoice = self.config['mutator'][self.currentFuzzerIndex]
            fuzzerData = mutators[ fuzzerChoice ]
            fuzzedCorpusData = self.normalFuzz(corpusData, fuzzerData)
            self.currentFuzzerIndex = (self.currentFuzzerIndex + 1) % len(self.config['mutator'])
            n += 1
            if n == len(self.config['mutator']):
                break

        return fuzzedCorpusData


    def normalFuzz(self, corpusData, fuzzerData):
        if 'file' in fuzzerData:
            return self._fuzzFile(corpusData, fuzzerData)
        elif 'class' in fuzzerData:
            return self._fuzzClass(corpusData, fuzzerData)
        else:
            logging.error("Hmmm")


    def _fuzzFile(self, corpusData, fuzzerData):
        self.fuzzingInFile = os.path.join(
            self.config["temp_dir"],
            str(self.seed) + ".in.raw")
        self.fuzzingOutFile = os.path.join(
            self.config["temp_dir"],
            str(self.seed) + ".out.raw")

        corpusDataNew = corpusData.createFuzzChild(self.seed)
        # we just randomly select a message to fuzz here
        # the fuzzer itself cannot have any information about the data
        # structures, so we select the data for him. Unlike in the
        # class based fuzzer
        corpusDataNew.networkData.selectMessage()
        initialData = corpusDataNew.networkData.getFuzzMessageData()

        self._writeDataToFile(initialData)
        self._runFuzzer(fuzzerData)
        fuzzedData = self._readDataFromFile()
        corpusDataNew.networkData.setFuzzMessageData(fuzzedData)
        corpusDataNew.fuzzer = fuzzerData['name']
        corpusDataNew.createNewFilename()  # update filename with fuzzmsgidx/seed

        return corpusDataNew


    def _fuzzClass(self, corpusData, fuzzerData):
        """Generic class-based fuzzer interface."""

        # each fuzzer is only instantiated once
        # if the fuzzer has to keep state for the individual corpusData,
        # it will do so by itself.
        if fuzzerData['class'] not in self.fuzzerClassInstances:
            fuzzerClass = str_to_class(fuzzerData['class'])
            fuzzerClassInstance = fuzzerClass(
                self.threadId,
                self.seed,
                self.config['target_dir'],
                threadCount=self.config['processes'])
            self.fuzzerClassInstances[ fuzzerData['class'] ] = fuzzerClassInstance

        corpusDataNew = self.fuzzerClassInstances[ fuzzerData['class'] ].fuzz(corpusData)
        if corpusDataNew is not None:
            corpusDataNew.fuzzer = fuzzerData['name']
            corpusDataNew.createNewFilename()  # update filename with fuzzmsgidx/seed

        return corpusDataNew


    # The classes below are only for external (file-) fuzzers.
    # It might make sense to split this class.


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


    def _runFuzzer(self, fuzzerData):
        """Call external fuzzer"""
        logging.info("Call mutator, seed: " + str(self.seed))

        args = fuzzerData["args"] % ({
            "seed": self.seed,
            "grammar": self.grammars_string,
            "input": self.fuzzingInFile,
            "output": self.fuzzingOutFile})

        logging.debug("Mutator command args: " + args)
        subprocess.call(self.fuzzerBin + " " + args, shell=True)

        return True
