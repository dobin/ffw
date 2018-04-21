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


    def addNewcorpusData(self, corpusData):
        """This fuzzer found a new corpus."""
        corpusData.writeToFile()
        self._addCorpusData(corpusData)


    def readNewcorpusData(self, filename):
        """Another fuzzer found a new corpus."""
        corpusData = CorpusData(self.config, filename=filename)
        corpusData.readFromFile()
        self._addCorpusData(corpusData)


    def loadCorpusFiles(self):
        """Load all initial corpus files from in/."""
        inputFiles = glob.glob(os.path.join(self.config["inputs"], '*'))
        for inputFile in inputFiles:
            filename = os.path.basename(inputFile)
            corpusData = CorpusData(
                self.config,
                filename=filename)
            corpusData.readFromFile()
            self._addCorpusData(corpusData)

        print("Input corpus files loaded: " + str(len(self.corpus)))


    def getRandomCorpus(self):
        return random.choice(self.corpus)
