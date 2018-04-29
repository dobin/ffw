#!/usr/bin/env python

import pickle
import logging
import os
import copy

from networkdata import NetworkData
from utils import xstr, filenameWithoutExtension, shortSeed


class CorpusData(object):
    """Dual: Corpus or Fuzzed Data."""

    def __init__(self,
                 config,
                 filename=None,
                 networkData=None,
                 parentFilename=None,
                 seed=None):
        self.config = config  # Type: Dict

        self.filename = filename  # Type: String
        self.parentFilename = parentFilename  # Type: String
        self.networkData = networkData  # Type: NetworkData

        self.seed = seed  # Type: String
        self.time = None  # Type: String

        self.basePath = config["input_dir"]

        self._parent = None


    def getParentCorpus(self):
        return self._parent


    def createFuzzChild(self, seed):
        corpusData = copy.deepcopy(self)
        corpusData.parentFilename = self.filename
        corpusData._parent = self
        corpusData.seed = seed
        corpusData.networkData.selectMessage()

        corpusData.createNewFilename()
        return corpusData


    def createNewFilename(self):
        self.filename = filenameWithoutExtension(self.filename)
        self.filename += '.' + shortSeed(self.seed)
        self.filename += '_m' + str(self.networkData.getFuzzMessageIndex())
        self.filename += '.pickle'


    def getRawData(self):
        rawData = {
            'filename': self.filename,
            'parentFilename': self.parentFilename,
            'networkData': self.networkData.getRawData(),
            'seed': self.seed,
            'time': self.time,
        }
        return rawData


    def setRawData(self, rawData):
        self.filename = rawData['filename']
        self.parentFilename = rawData['parentFilename']
        self.seed = rawData['seed']
        self.time = rawData['time']
        self.networkData = NetworkData(self.config, rawData['networkData'])


    def writeToFile(self):
        rawData = self.getRawData()
        path = os.path.join(self.basePath, self.filename)
        logging.debug("Write corpus to file: " + path)
        with open(path, 'w') as outfile:
            pickle.dump(rawData, outfile)


    def readFromFile(self):
        filepath = os.path.join(self.basePath, self.filename)
        with open(filepath, 'r') as infile:
            rawData = pickle.load(infile)
            self.setRawData(rawData)

        # check if no client message is found in an input
        if next((i for i in self.networkData.messages if i["from"] == "cli"), None) is None:
            raise ValueError("No client messages found in %s" % self.filename)


    def __str__(self):
        s = ""
        s += "Filename: " + xstr(self.filename) + "\n"
        s += "NetworkData: \n" + xstr(self.networkData) + "\n"
        s += "Seed: " + xstr(self.seed) + "\n"
        s += "Time: " + xstr(self.time) + "\n"
        return s
