#!/usr/bin/env python

import pickle
import logging
import os

from networkdata import NetworkData
from utils import xstr


class CorpusData(object):

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
        with open(path, 'w') as outfile:
            pickle.dump(rawData, outfile)


    def readFromFile(self):
        filepath = os.path.join(self.basePath, self.filename)
        with open(filepath, 'r') as infile:
            rawData = pickle.load(infile)

            if 'parentFilename' in rawData:
                self.parentFilename = rawData["parentFilename"]
            self.networkData = NetworkData(self.config, rawData["networkData"])
            self.seed = rawData["seed"]
            self.time = rawData["time"]

        # check if no client message is found in an input
        if next((i for i in self.networkData.messages if i["from"] == "cli"), None) is None:
            raise ValueError("No client messages found in %s" % self.filename)


    def __str__(self):
        s = ""
        s += "Filename: " + xstr(self.filename) + "\n"
        s += "Parent Filename: " + xstr(self.parentFilename) + "\n"
        s += "NetworkData: \n" + xstr(self.networkData) + "\n"
        s += "Seed: " + xstr(self.seed) + "\n"
        s += "Time: " + xstr(self.time) + "\n"
        return s