#!/usr/bin/env python

import pickle
import os
import logging
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
            self.filename += '.' + utils.shortSeed(self.corpusData.seed)
            self.filename += '_' + str(self.corpusData.networkData.getFuzzMessageIndex())
            self.filename += '.crash'

        # our parent spawned us - attribute it to them
        if corpusData is not None and corpusData.getParentCorpus() is not None:
            corpusData.getParentCorpus().statsAddCrash()

        # should we write a .txt file additional to the pickle?
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
            "filename": self.filename,
            "asanOutput": self.asanOutput,
            "signum": self.signum,
            "exitcode": self.exitcode,

            "reallydead": self.reallydead,
            "serverpid": self.serverpid,
            "fuzzerPos": self.fuzzerPos,

            "corpusData": self.corpusData.getRawData(),
        }

        return crashDataRaw


    def setRawData(self, rawData):
        self.asanOutput = rawData['asanOutput']
        self.signum = rawData['signum']
        self.exitcode = rawData['exitcode']
        self.reallydead = rawData['reallydead']
        self.serverpid = rawData['serverpid']
        self.fuzzerPos = rawData['fuzzerPos']

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
