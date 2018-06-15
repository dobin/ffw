#!/usr/bin/env python

import os
import random
import glob
import logging

from corpusdata import CorpusData


class CorpusManager(object):
    """
    Manage the corpusDatas
    """

    def __init__(self, config):
        self.corpus = []  # type: Array[corpusData]
        self.config = config  # type: Dict


    def __iter__(self):
        return CorpusFileIterator(self.corpus)


    def _addCorpusData(self, corpusData):
        self.corpus.append(corpusData)


    def loadCorpusFiles(self):
        """Load all initial corpus files from in/."""
        inputFiles = glob.glob(os.path.join(self.config["input_dir"], '*.pickle'))
        for inputFile in inputFiles:
            filename = os.path.basename(inputFile)
            corpusData = self._createCorpusData(filename)
            corpusData.readFromFile()
            self._addCorpusData(corpusData)

        logging.info("Input corpus files loaded: " + str(len(self.corpus)))


    def _createCorpusData(self, filename):
        """
        Create A corpus data object.

        It is necessary to overwrite this function in HonggCorpusManager
        to create HonggCorpusData insted of CorpusData...
        """
        corpusData = CorpusData(
            self.config,
            filename=filename)
        return corpusData


    def getRandomCorpus(self):
        return random.choice(self.corpus)


    def getCorpusCount(self):
        return len(self.corpus)


    def getMaxLatency(self):
        max = 0
        for corpus in self.corpus:
            if corpus.networkData.getMaxLatency() > max:
                max = corpus.networkData.getMaxLatency()

        return max


    def getTimeoutCount(self):
        timeoutCount = 0
        for corpus in self.corpus:
            for message in corpus.networkData.messages:
                timeoutCount += message["timeouts"]

        return timeoutCount



class CorpusFileIterator(object):
    """The iter() of CorpusManager class."""

    def __init__(self, corpuses):
        self.corpuses = corpuses
        self.current = 0

    def __iter__(self):
        return self

    def next(self):
        if self.current >= len(self.corpuses):
            raise StopIteration
        else:
            self.current += 1
            return self.corpuses[self.current - 1]
