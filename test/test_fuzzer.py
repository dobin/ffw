#!/usr/bin/env python

import unittest
import os

from common.corpusdata import CorpusData
from common.networkdata import NetworkData
from fuzzer.fuzzerinterface import FuzzerInterface


class CorpusFileTest(unittest.TestCase):
    def _getConfig(self):
        config = {
            "inputs": "/tmp/",
            "temp_dir": "/tmp/",
            "basedir": os.path.dirname(os.path.realpath(__file__)) + "/..",
        }
        print "A: " + os.path.dirname(os.path.realpath(__file__))

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
        corpusData = CorpusData(config, 'data0', networkData)
        return corpusData


    def test_dumbfuzzer(self):
        config = self._getConfig()
        config['fuzzer'] = 'Dumb'
        fuzzerInterface = FuzzerInterface(config)

        corpusData = self._getCorpusData(config)
        fuzzedCorpusData = fuzzerInterface.fuzz(corpusData)

        # note that we only have one cli message, which is at index 0
        self.assertNotEqual(corpusData.networkData.messages[0]['data'],
                            fuzzedCorpusData.networkData.messages[0]['data'])


    def test_radamsafuzzer(self):
        config = self._getConfig()
        config['fuzzer'] = 'Radamsa'
        fuzzerInterface = FuzzerInterface(config)

        corpusData = self._getCorpusData(config)
        fuzzedCorpusData = fuzzerInterface.fuzz(corpusData)

        # note that we only have one cli message, which is at index 0
        self.assertNotEqual(corpusData.networkData.messages[0]['data'],
                            fuzzedCorpusData.networkData.messages[0]['data'])


if __name__ == '__main__':
    unittest.main()
