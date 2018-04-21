import copy
import random

class MockupFuzzer(object):
    def __init__(self, config):
        self.config = config
        self.seed = self._generateSeed()


    def _generateSeed(self):
        self.seed = random.randint(0, 2**64 - 1)


    def fuzz(self, corpusData):
        corpusDataNew = copy.deepcopy(corpusData)

        corpusDataNew.networkData.selectMessage()
        msg = corpusDataNew.networkData.getFuzzMessageData()
        msg += "A"
        corpusDataNew.networkData.setFuzzMessageData(msg)
        return corpusDataNew
