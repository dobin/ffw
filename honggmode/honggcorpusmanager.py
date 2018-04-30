#!/usr/bin/env python2

import logging
import pyinotify
import time
import os
import utils

from honggcorpusdata import HonggCorpusData
from common.corpusmanager import CorpusManager


class HonggCorpusManager(CorpusManager):
    """Manage the corpus files for the fuzzer."""

    def __init__(self, config):
        super(self.__class__, self).__init__(config)
        self.fileWatcher = FileWatcher(config, self)


    def addNewCorpusData(self, honggCorpusData):
        """This fuzzer found a new corpus."""
        self._addCorpusData(honggCorpusData)
        honggCorpusData.writeToFile()


    def readNewCorpusData(self, filename):
        """Another fuzzer found a new corpus."""
        # we are notified when the file is created, not when it is written
        # Wait here till it has data
        fileSize = 0
        while fileSize is 0:
            st = os.stat(filename)
            fileSize = st.st_size
            time.sleep(0.1)

        corpusData = HonggCorpusData(
            self.config,
            filename=filename,
            networkData=None,
            processed=False,
            isExternal=True)
        corpusData.readFromFile()
        self._addCorpusData(corpusData)


    def loadCorpusFiles(self):
        """Not only load, but also fix all the references."""
        super(self.__class__, self).loadCorpusFiles()

        for corpus in self:
            if corpus.parentFilename is not None:
                corpus._parent = self._getCorpusByFilename(corpus.parentFilename)


    def hasNewExternalCorpus(self):
        for corpus in self.corpus:
            if not corpus.isProcessed():
                return True

        return False


    def getNewExternalCorpus(self):
        for corpus in self.corpus:
            if not corpus.isProcessed():
                return corpus

        return None


    def _getCorpusByFilename(self, filename):
        for corpus in self.corpus:
            if corpus.filename == filename:
                return corpus

        return None


    def _findCorpusByFilename(self, filename):
        for corpus in self.corpus:
            if corpus.filename == filename:
                return True

        return False


    def startWatch(self):
        self.fileWatcher.start()


    def checkForNewFiles(self):
        self.fileWatcher.checkForEvents()


    def newFileHandler(self, filepath):
        # Note that we receive a complete file path
        # But we usually require the filename
        filename = os.path.basename(filepath)

        if not self._findCorpusByFilename(filename):
            self.readNewCorpusData(filepath)


    def printStats(self):
        for idx, corpus in enumerate(self.corpus):
            d = (
                idx,
                utils.shortSeed(corpus.seed),
                utils.xstr(self._getIdxOfCorpus(corpus._parent)),
                utils.xstr(corpus.networkData.getFuzzMessageIndex()),
                corpus.stats["new"],
                corpus.stats["crashes"])
            print "    Corpus %3d  (%5s):  Parent: %3s  Msg: %3s  Children: %3d  Crashes: %3d" % d


    def _getIdxOfCorpus(self, theCorpus):
        for idx, corpus in enumerate(self.corpus):
            if corpus is theCorpus:
                return idx

        return None


    def _createCorpusData(self, filename):
        """
        Create A hongg corpus data object.

        It is necessary to overwrite this function in HonggCorpusManager
        to create HonggCorpusData instead of CorpusData
        """
        corpusData = HonggCorpusData(
            self.config,
            filename=filename)
        return corpusData


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
        watchPath = self.config["input_dir"]
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
        self.corpusManager.newFileHandler(event.pathname)
