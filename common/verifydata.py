#!/usr/bin/env python2

import pickle
import os
import logging
import utils

from common.crashdata import CrashData


class VerifyData(object):

    def __init__(self,
                 config,
                 crashData=None,
                 filename=None,
                 faultaddress=0,
                 backtrace=None,
                 cause=None,
                 analyzerOutput=None,
                 analyzerType=None):
        self.config = config
        self.crashData = crashData

        if analyzerType is not None:
            self.analyzerType = analyzerType
        else:
            self.analyzerType = ''

        if filename is not None:
            self.filename = filename
        elif crashData is not None:
            self.filename = utils.filenameWithoutExtension(crashData.filename)
            self.filename += "." + self.analyzerType
            self.filename += '.verified'
        else:
            self.filename = None

        self.faultaddress = faultaddress
        self.backtrace = backtrace
        self.cause = cause
        self.analyzerOutput = analyzerOutput


        self.processStdout = None


    def getRawData(self):
        verifyDataRaw = {
            'filename': self.filename,
            'faultaddress': self.faultaddress,
            'backtrace': self.backtrace,
            'cause': self.cause,
            'analyzerOutput': self.analyzerOutput,
            'analyzerType': self.analyzerType,
            'processStdout': self.processStdout,

            'crashData': self.crashData.getRawData(),
        }
        return verifyDataRaw


    def setRawData(self, rawData):
        self.crashData = CrashData(self.config)
        self.crashData.setRawData(rawData['crashData'])

        self.filename = rawData['filename']
        self.faultaddress = rawData['faultaddress']
        self.backtrace = rawData['backtrace']
        self.cause = rawData['cause']
        self.analyzerOutput = rawData['analyzerOutput']
        self.analyzerType = rawData['analyzerType']
        self.processStdout = rawData['processStdout']


    def writeToFile(self):
        data = self.getRawData()
        filepath = os.path.join(self.config["verified_dir"], self.filename)

        with open(filepath, 'w') as f:
            pickle.dump(data, f)


    def readFromFile(self):
        filepath = os.path.join(self.config["verified_dir"], self.filename)

        with open(filepath, 'r') as f:
            rawData = pickle.load(f)
            self.setRawData(rawData)


    def __str__(self):
        d = ""
        d += "VerifyCrashData: " + "Faultaddress: " + str(self.faultAddress)

        if self.backtrace:
            d += " Has_Backtrace"
        else:
            d += " NO_Backtrace"

        if self.cause:
            d += " Has_Cause"
        else:
            d += " NO_Cause"

        if self.analyzerOutput:
            d += " Has_AnalyzerOutput"
        else:
            d += " NO_AnalyzerOutput"

        d += "\n"

        return d
