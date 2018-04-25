#!/usr/bin/env python

import glob
import os
import logging

from verifydata import VerifyData


class VerifyManager(object):
    """Manage the verifydata files."""

    def __init__(self, config):
        self.verify = []  # type: Array[verifyData]
        self.config = config  # type: Dict


    def __iter__(self):
        return VerifyFileIterator(self.verify)


    def _addVerifyData(self, verifyData):
        self.verify.append(verifyData)


    def loadVerifiedFiles(self):
        """Load all initial verify files from out/."""
        inputFiles = glob.glob(os.path.join(self.config["verified_dir"], '*.verified'))
        for inputFile in inputFiles:
            filename = os.path.basename(inputFile)
            verifyData = self._createVerifyData(filename)
            verifyData.readFromFile()
            self._addVerifyData(verifyData)

        logging.info("Input verify files loaded: " + str(len(self.verify)))


    def _createVerifyData(self, filename):
        verifyData = VerifyData(
            self.config,
            filename=filename)
        return verifyData


    def getVerifiedCount(self):
        return len(self.verify)


class VerifyFileIterator(object):
    """The iter() of CorpusManager class."""

    def __init__(self, verifyes):
        self.verifyes = verifyes
        self.current = 0

    def __iter__(self):
        return self

    def next(self):
        if self.current >= len(self.verifyes):
            raise StopIteration
        else:
            self.current += 1
            return self.verifyes[self.current - 1]
