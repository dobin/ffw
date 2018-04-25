#!/usr/bin/env python

import glob
import os
import logging

from crashdata import CrashData


class CrashManager(object):
    """Manage the crashdata files."""

    def __init__(self, config):
        self.crash = []  # type: Array[crashData]
        self.config = config  # type: Dict


    def __iter__(self):
        return CrashFileIterator(self.crash)


    def _addCrashData(self, crashData):
        self.crash.append(crashData)


    def loadCrashFiles(self):
        """Load all initial crash files from out/."""
        inputFiles = glob.glob(os.path.join(self.config["outcome_dir"], '*.crash'))
        for inputFile in inputFiles:
            filename = os.path.basename(inputFile)
            crashData = self._createCrashData(filename)
            crashData.readFromFile()
            self._addCrashData(crashData)

        logging.info("Input crash files loaded: " + str(len(self.crash)))


    def _createCrashData(self, filename):
        crashData = CrashData(
            self.config,
            filename=filename)
        return crashData


    def getCrashCount(self):
        return len(self.crash)


class CrashFileIterator(object):
    """The iter() of CorpusManager class."""

    def __init__(self, crashes):
        self.crashes = crashes
        self.current = 0

    def __iter__(self):
        return self

    def next(self):
        if self.current >= len(self.crashes):
            raise StopIteration
        else:
            self.current += 1
            return self.crashes[self.current - 1]
