#!/usr/bin/env python

import unittest

from common.networkdata import NetworkData
from common.corpusdata import CorpusData
from mockupfuzzer import MockupFuzzer


class CorpusFileTest(unittest.TestCase):
    def _getConfig(self):
        config = {
            "input_dir": "/tmp/",
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


    def _getNetworkDataNoCli(self, config):
        networkMessages = [
            {
                'data': 'msg 1 srv',
                'from': 'srv',
                'index': 0,
            }
        ]

        networkData = NetworkData(config,
                                  networkMessages)
        return networkData


    def test_readwrite(self):
        """Test if writing+reading file works."""
        config = self._getConfig()
        networkData = self._getNetworkData(config)
        filename = "test"

        corpusData1 = CorpusData(config, filename, networkData)
        corpusData1.writeToFile()

        corpusData2 = CorpusData(config, filename)
        corpusData2.readFromFile()

        self.assertEqual(corpusData1.networkData.messages[0]['data'],
                         corpusData2.networkData.messages[0]['data'])


    def test_missingclimsg(self):
        """Test fail-on missing cli message (need one to fuzz)."""
        config = self._getConfig()
        networkData = self._getNetworkDataNoCli(config)
        filename = "test"

        corpusData1 = CorpusData(config, filename, networkData)
        corpusData1.writeToFile()

        corpusData2 = CorpusData(config, filename)
        self.assertRaises(ValueError, corpusData2.readFromFile)


    def test_fuzz(self):
        """Try to fuzz and check if it worked."""
        config = self._getConfig()
        networkData = self._getNetworkData(config)
        fuzzer = MockupFuzzer(config)
        filename = "test"

        corpusDataParent = CorpusData(config, filename, networkData)
        corpusDataChild = fuzzer.fuzz(corpusDataParent)

        # note that we only have one cli message, which is at index 0
        self.assertNotEqual(corpusDataParent.networkData.messages[0]['data'],
                            corpusDataChild.networkData.messages[0]['data'])


if __name__ == '__main__':
    unittest.main()
