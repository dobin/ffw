#!/bin/python

import pickle
import os
import utils

from common.corpusdata import CorpusData


class CrashData():

    def __init__(self,
                 config,
                 corpusData=None,
                 fuzzerPos=None,
                 filename=None):
        self.config = config
        self.corpusData = corpusData
        self.fuzzerPos = fuzzerPos

        if filename is not None:
            self.filename = filename
        elif corpusData is not None:
            self.filename = utils.filenameWithoutExtension(corpusData.filename)
            self.filename += '_' + self.corpusData.seed
            self.filename += '.crash'

        self.writeTxt = False

        self.asanOutput = None
        self.signum = None
        self.exitcode = None
        self.reallydead = None
        self.serverpid = None


    def setCrashInformation(self, asanOutput=None, signum=None, exitcode=None, reallydead=None, serverpid=None):
        self.asanOutput = asanOutput
        self.signum = signum
        self.exitcode = exitcode
        self.reallydead = reallydead
        self.serverpid = serverpid


    def getRawData(self):
        crashDataRaw = {
            "asanOutput": self.asanOutput,
            "signum": self.signum,
            "exitcode": self.exitcode,

            "reallydead": self.reallydead,
            "serverpid": self.serverpid,
            "fuzzerPos": self.fuzzerPos,
        }

        data = {
            "crashData": crashDataRaw,
            "corpusData": self.corpusData.getRawData(),
        }

        return data


    def setRawData(self, rawData):
        self.asanOutput = rawData['crashData']['asanOutput']
        self.signum = rawData['crashData']['signum']
        self.exitcode = rawData['crashData']['exitcode']
        self.reallydead = rawData['crashData']['reallydead']
        self.serverpid = rawData['crashData']['serverpid']
        self.fuzzerPos = rawData['crashData']['fuzzerPos']

        self.corpusData = CorpusData(self.config)
        self.corpusData.setRawData(rawData['corpusData'])


    def writeToFile(self):
        seed = self.corpusData.seed
        data = self.getRawData()
        filepath = os.path.join(self.config["outcome_dir"], self.filename)

        with open(filepath, 'w') as f:
            pickle.dump(data, f)

        if self.writeTxt:
            with open(os.path.join(self.config["outcome_dir"], self.filename + '.txt'), 'w') as f:
                f.write("Seed: %s\n" % seed)
                f.write("Fuzzer: %s\n" % self.config["fuzzer"])
                f.write("Target: %s\n" % self.config["target_bin"])

                f.write("Fuzzerpos: %s\n" % self.fuzzerPos)
                f.write("Signal: %d\n" % self.signum)
                f.write("Exitcode: %d\n" % self.exitcode)
                f.write("Reallydead: %s\n" % str(self.reallydead))
                f.write("PID: %s\n" % str(self.serverpid))
                f.write("Asanoutput: %s\n" % self.asanOutput)


    def readFromFile(self):
        filepath = os.path.join(self.config["outcome_dir"], self.filename)

        with open(filepath, 'r') as f:
            rawData = pickle.load(f)
            self.setRawData(rawData)
