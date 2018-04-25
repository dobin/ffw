#!/usr/bin/env python

import unittest
import time

from common.networkdata import NetworkData
from common.corpusdata import CorpusData
from common.crashdata import CrashData
import testutils


class CrashDataTest(unittest.TestCase):
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
        corpusData = CorpusData(config, 'data_0.corpus', networkData, seed="42")
        return corpusData


    def test_writeread(self):
        config = self._getConfig()
        testutils.prepareFs(config)

        # get some example corpus
        corpusData = self._getCorpusData(config)

        # assume this corpus crashed the server
        crashData = CrashData(config, corpusData)
        crashData.setCrashInformation(asanOutput="meh")

        # write it
        crashData.writeToFile()

        # try to read it again
        crashData2 = CrashData(config, filename=crashData.filename)
        crashData2.readFromFile()

        # test an example of each layer
        self.assertEqual(
            crashData.asanOutput,
            crashData2.asanOutput)
        self.assertEqual(
            crashData.corpusData.filename,
            crashData2.corpusData.filename)
        self.assertEqual(
            crashData.corpusData.networkData.messages[0]['data'],
            crashData2.corpusData.networkData.messages[0]['data'],
        )


if __name__ == '__main__':
    unittest.main()
