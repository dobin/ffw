
import os
import logging
import pickle
import pyinotify
import time
import random
import glob

from . import corpusfile


class CorpusManager(object):
    """
    Manage the corpus files for the fuzzer.

    """

    def __init__(self, config):
        self.corpus = []
        self.config = config
        self.fileWatcher = FileWatcher(config, self)


    def getRandomCorpus(self):
        c = random.randint(0, len(self.corpus) - 1)

        idata = self.corpus[c].data
        logging.info("--[ Fuzz corpus: " + str(c) + "  size: " + str(len(self.corpus)))
        return idata


    def addNewCorpusFile(self, data, seed):
        """
        Add new corpus file (identified by fuzzer) to the directory.

        Note that it will be loaded later by the watcher.
        """
        logging.info("CorpusManager: addNewCorpusFile: " + str(seed))

        filename = self.config["inputs"] + "/" + str(seed) + ".corpus"
        with open(filename, 'wb') as f:
            pickle.dump(data, f)


    def initialLoad(self):
        """
        Load initial recorded pickle files.

        Load the initial recorded data files, plus the added corpus
        files.
        """
        inputFiles = glob.glob(os.path.join(self.config["inputs"], '*'))

        for inputFile in inputFiles:
            #file = self.config["inputs"] + "/data_0.pickle"
            self.loadFile(inputFile)


    def loadFile(self, fileName):
        logging.debug("Load Corpus file: " + fileName)
        if not os.path.isfile(fileName):
            logging.error("Could not read input file: " + fileName)
            return False

        with open(fileName, 'rb') as f:
            data = pickle.load(f)

        corpusFile = corpusfile.CorpusFile(fileName, data)

        self.corpus.append(corpusFile)


    def startWatch(self):
        self.fileWatcher.start()


    def checkForNewFiles(self):
        self.fileWatcher.checkForEvents()


    def newFileHandler(self, filename):
        self.loadFile(filename)


class FileWatcher(object):
    """
    Abstract pyinotify away.

    Watches directory, will call corpusManager.newFileHandler() if any new.
    """

    def __init__(self, config, corpusManager):
        self.wm = pyinotify.WatchManager()
        self.mask = pyinotify.IN_CREATE
        self.handler = FileWatcherEventHandler(corpusManager)
        self.wdd = None
        self.config = config


    def start(self):
        watchPath = self.config["inputs"]
        self.notifier = pyinotify.Notifier(self.wm, self.handler, timeout=10)
        self.wdd = self.wm.add_watch(watchPath, self.mask, rec=False)


    def checkForEvents(self):
        self.notifier.process_events()
        while self.notifier.check_events():
            self.notifier.read_events()
            self.notifier.process_events()


class FileWatcherEventHandler(pyinotify.ProcessEvent):
    """
    File handler for pyinotify.

    Calls corpusManager.newFileHandler() if new file appears.
    """

    def __init__(self, corpusManager):
        self.corpusManager = corpusManager


    def process_IN_CREATE(self, event):
        print "Creating:", event.pathname
        self.corpusManager.newFileHandler(event.pathname)


if __name__ == "__main__":
    corpusManager = CorpusManager()
    corpusManager.start()
    while True:
        time.sleep(1)
        corpusManager.checkForNewFiles()
