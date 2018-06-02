#!/usr/bin/env python

import copy
import random


class MockupFuzzer(object):
    def __init__(self, config):
        self.config = config
        self.seed = self._generateSeed()


    def _generateSeed(self):
        return "1"


    def fuzz(self, corpusData):
        corpusDataNew = corpusData.createFuzzChild(self.seed)
        corpusDataNew.networkData.selectMessage()
        msg = corpusDataNew.networkData.getFuzzMessageData()
        msg += "A"
        corpusDataNew.networkData.setFuzzMessageData(msg)
        corpusDataNew.createNewFilename()  # update filename with fuzzmsgidx
        return corpusDataNew
