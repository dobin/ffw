import os
import random
import glob

from corpusdata import CorpusData


class CorpusManager(object):
    """
    Manage the corpusDatas
    """

    def __init__(self, config):
        self.corpus = []  # type: Array[corpusData]
        self.config = config  # type: Dict


    def _addCorpusData(self, corpusData):
        self.corpus.append(corpusData)


    def loadCorpusFiles(self):
        """Load all initial corpus files from in/."""
        inputFiles = glob.glob(os.path.join(self.config["inputs"], '*'))
        for inputFile in inputFiles:
            filename = os.path.basename(inputFile)
            corpusData = self._createCorpusData(filename)
            corpusData.readFromFile()
            self._addCorpusData(corpusData)

        print("Input corpus files loaded: " + str(len(self.corpus)))


    def _createCorpusData(self, filename):
        """
        Create A corpus data object.

        It is necessary to overwrite this function in HonggCorpusManager
        to create HonggCorpusData...
        """
        corpusData = CorpusData(
            self.config,
            filename=filename)
        return corpusData


    def getRandomCorpus(self):
        return random.choice(self.corpus)


    def getCorpusCount(self):
        return len(self.corpus)
