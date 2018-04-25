#!/usr/bin/env python

import unittest
import os

from common.networkdata import NetworkData
from common.corpusdata import CorpusData
from common.crashdata import CrashData
from common.crashmanager import CrashManager

import testutils


class CrashManagerTest(unittest.TestCase):
    def _getConfig(self):
        config = {
            "input_dir": "/tmp/ffw-test/in",
            "outcome_dir": "/tmp/ffw-test/out",
            "fuzzer": "Myfuzzer",
            "target_bin": "bin/mytarget"
        }
        return config


    def _getNetworkData(self, config):
        networkMessages = [
            {
                'data': 'msg 1 cli',
                'from': 'cli',
                'index': 0,
            },
            {
                'data': 'msg 2 srv',
                'from': 'srv',
                'index': 1,
            }
        ]

        networkData = NetworkData(config,
                                  networkMessages)
        return networkData


    def _getCorpusData(self, config):
        networkData = self._getNetworkData(config)
        corpusData = CorpusData(config, 'data0', networkData, seed="42")
        return corpusData


    def _getCrashData(self, config):
        corpusData = self._getCorpusData(config)
        crashData = CrashData(config, corpusData)
        return crashData


    def test_loadfiles(self):
        """Test if we can load the initial corpus."""
        config = self._getConfig()
        testutils.prepareFs(config)

        # write an crashdata file
        crashData = self._getCrashData(config)
        crashData.writeToFile()

        # load all corpus files
        crashManager = CrashManager(config)
        crashManager.loadCrashFiles()
        self.assertEqual(crashManager.getCrashCount(), 1)


if __name__ == '__main__':
    unittest.main()
