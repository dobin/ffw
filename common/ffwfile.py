#!/usr/bin/env python2

import pickle

from common.corpusdata import CorpusData
from common.crashdata import CrashData
from common.verifydata import VerifyData


class FfwFile(object):
    def __init__(self, config):
        self.config = config


    def getNetworkData(self, filepath):
        data = self._readPickleFile(filepath)

        if 'networkData' in data:
            corpusData = CorpusData(self.config)
            corpusData.setRawData(data)
            return corpusData.networkData

        if 'corpusData' in data:
            crashData = CrashData(self.config)
            crashData.setRawData(data)
            return crashData.corpusData.networkData

        if 'crashData' in data:
            verifyData = VerifyData(self.config)
            verifyData.setRawData(data)
            return verifyData.crashData.corpusData.networkData

        return None


    def _readPickleFile(self, fileName):
        data = None

        with open(fileName, 'rb') as f:
            data = pickle.load(f)

        return data
