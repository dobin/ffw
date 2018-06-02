#!/usr/bin/env python

import unittest
import os

from common.corpusdata import CorpusData
from common.networkdata import NetworkData
from mutator.mutatorinterface import MutatorInterface, testMutatorConfig
import testutils


class CorpusFileTest(unittest.TestCase):
    def _getConfig(self):
        config = {
            "input_dir": "/tmp/ffw-test/in",
            "temp_dir": "/tmp/ffw-test/temp",
            "basedir": os.path.dirname(os.path.realpath(__file__)) + "/..",
        }

        return config


    def _getNetworkData(self, config):
        networkMessages = [
            {
                'data': 'msg 1 cli AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
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
        config['mutator'] = [ 'Dumb' ]
        self.assertTrue(testMutatorConfig(config, 'basic'))
        mutatorInterface = MutatorInterface(config, 0)

        corpusData = self._getCorpusData(config)
        fuzzedCorpusData = mutatorInterface.fuzz(corpusData)

        # note that we only have one cli message, which is at index 0
        self.assertNotEqual(corpusData.networkData.messages[0]['data'],
                            fuzzedCorpusData.networkData.messages[0]['data'])


    def test_radamsafuzzer(self):
        config = self._getConfig()
        config['mutator'] = [ 'Radamsa' ]
        self.assertTrue(testMutatorConfig(config, 'basic'))
        mutatorInterface = MutatorInterface(config, 0)

        corpusData = self._getCorpusData(config)
        fuzzedCorpusData = mutatorInterface.fuzz(corpusData)

        # note that we only have one cli message, which is at index 0
        self.assertNotEqual(corpusData.networkData.messages[0]['data'],
                            fuzzedCorpusData.networkData.messages[0]['data'])


if __name__ == '__main__':
    unittest.main()
