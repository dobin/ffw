#!/usr/bin/env python2

import urllib
import random
import logging
import os
import subprocess
import copy
import time
import sys

fuzzers = {
    "Dumb":
    {
        "name": "Dumb",
        "file": "fuzzer_dumb.py",
        "args": '%(seed)s "%(input)s" %(output)s',
    },
    "Radamsa":
    {
        "name": "Radamsa",
        "file": "radamsa/bin/radamsa",
        "args": '-s %(seed)s -o %(output)s "%(input)s"',
    },
}


class FuzzingIterationData(object):
    """
    Contains all the data for a fuzzing iteration.

    This includes:
    - all the original packets
    - the fuzzed packet
    - seed
    """

    def __init__(self, config, initialData):
        self.seed = None
        self.config = config
        self.initialData = initialData
        self.fuzzedData = None
        self.choice = None
        self.fuzzingInFile = None
        self.time = time.strftime("%c")


    def getData(self):
        """
        Return all necessary data.

        Used by fuzzing slave to export data to pickle file.
        """
        data = {
            "seed": self.seed,
            # "config": self.config,
            "initialData": self.initialData,
            "fuzzedData": self.fuzzedData,
            "time": self.time,
        }
        return data


    def _generateSeed(self):
        """Generate a random seed to pass to the fuzzer."""
        self.seed = random.randint(0, 2**64 - 1)


    def fuzzData(self):
        """
        Creates self.fuzzedData.

        By selecting a message, and mutate it by calling a fuzzer
        returns False if something went wrong
        """
        logging.debug("Fuzzing the data")

        self._generateSeed()
        self._chooseInput()

        self.fuzzingInFile = os.path.join(self.config["temp_dir"], str(self.seed) + ".in.raw")
        self.fuzzingOutFile = os.path.join(self.config["temp_dir"], str(self.seed) + ".out.raw")

        if not self._writeFuzzingFile():
            return False

        if not self._runFuzzer():
            return False

        if not self._readFuzzingFile():
            return False

        return True


    def _writeFuzzingFile(self):
        """Write the data to be fuzzed to a file."""
        file = open(self.fuzzingInFile, "w")
        file.write(self.choice["data"])
        #logging.debug("urllib.quote_plus: " + str(self.choice["data"]))
        file.close()

        return True


    def _readFuzzingFile(self):
        """Read the fuzzed data"""
        file = open(self.fuzzingOutFile, "r")
        data = file.read()
        file.close()

        #m = self.fuzzedData.index(self.choice)
        #self.fuzzedData[m]["data"] = data
        self.choice["data"] = data
        self.choice["isFuzzed"] = True

        #logging.debug("OUTPUT: " + urllib.quote_plus(self.choice["data"]))

        try:
            os.remove(self.fuzzingInFile)
            os.remove(self.fuzzingOutFile)
        except:
            print "Failed to remove file %s!" % self.fuzzingInFile
            print "Failed to remove file %s!" % self.fuzzingOutFile

        return True


    def _runFuzzer(self):
        """Call external fuzzer"""
        logging.info("Call fuzzer, seed: " + str(self.seed))

        fuzzerData = fuzzers[ self.config["fuzzer"] ]
        if not fuzzerData:
            print "Could not find fuzzer with name: " + self.config["fuzzer"]
            return False

        fuzzerBin = self.config["basedir"] + "/" + fuzzerData["file"]
        if not os.path.isfile(fuzzerBin):
            print "Could not find fuzzer binary: " + fuzzerBin
            sys.exit()

        args = fuzzerData["args"] % ({
            "seed": self.seed,
            "input": self.fuzzingInFile,
            "output": self.fuzzingOutFile})
        subprocess.call(fuzzerBin + " " + args, shell=True)

        return True


    def _chooseInput(self):
        """Select a message to be fuzzed."""
        #self.fuzzedData = list(self.initialData)
        self.fuzzedData = copy.deepcopy(self.initialData)

        # TODO: make this dependant on seed
        if self.config["maxmsg"]:
            idx = random.randint(0, self.config["maxmsg"])
            self.choice = self.fuzzedData[idx]
            if self.choice["from"] != "cli":
                idx = random.randint(0, self.config["maxmsg"])
                self.choice = self.fuzzedData[idx]
        else:
            self.choice = random.choice(self.fuzzedData)
            while self.choice["from"] != "cli":
                self.choice = random.choice(self.fuzzedData)

        s = 'selected input: %s  from: %s  len: %s' % ( str(self.fuzzedData.index(self.choice)), self.choice["from"], str(len(self.choice["data"]) ) )
        logging.debug(s)
        #logging.debug("INPUT: " + urllib.quote_plus(self.choice["data"]))
