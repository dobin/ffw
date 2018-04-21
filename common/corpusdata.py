import json
import logging

from networkdata import *

class CorpusData(object):

    def __init__(self,
                 config,
                 filename=None,
                 networkData=None,
                 parentFilename=None):
        self.config = config  # Type: Dict

        self.filename = filename  # Type: String
        self.parentFilename = parentFilename  # Type: String

        self.networkData = networkData  # Type: NetworkData

        self.seed = None  # Type: String
        self.time = None  # Type: String

        self.basePath = config["inputs"]


    def writeToFile(self):
        rawData = {
            'parentFilename': self.parentFilename,

            'networkData': self.networkData.getRawData(),

            'seed': self.seed,
            'time': self.time,
        }

        with open(self.basePath + self.filename, 'w') as outfile:
            json.dump(rawData, outfile)


    def readFromFile(self):
        data = None

        with open(self.basePath + self.filename, 'r') as infile:
            rawData = json.load(infile)

            self.parentFilename = rawData["parentFilename"]
            self.networkData = NetworkData(self.config, rawData["networkData"])
            self.seed = rawData["seed"]
            self.time = rawData["time"]

        # check if no client message is found in an input
        if next((i for i in self.networkData.messages if i["from"] == "cli"), None) is None:
            logging.error("No client messages found in %s." % self.filename)
            raise ValueError("No client messages found in %s" % self.filename)
