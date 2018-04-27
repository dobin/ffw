#!/usr/bin/env python

import unittest
import os

from common.corpusdata import CorpusData
from common.networkdata import NetworkData
from mutator.mutatorinterface import MutatorInterface, testMutatorConfig
import testutils


class CorpusFileTest(unittest.TestCase):
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


    def test_dumbfuzzer(self):
        config = testutils.getConfig()
        config['mutator'] = 'Dumb'
        self.assertTrue(testMutatorConfig(config, testForInputFiles=False))
        mutatorInterface = MutatorInterface(config)

        corpusData = testutils.getCorpusData(
            config,
            networkData=self._getNetworkData(config))
        fuzzedCorpusData = mutatorInterface.fuzz(corpusData)

        # note that we only have one cli message, which is at index 0
        self.assertNotEqual(corpusData.networkData.messages[0]['data'],
                            fuzzedCorpusData.networkData.messages[0]['data'])


    def test_radamsafuzzer(self):
        config = testutils.getConfig()
        config['mutator'] = 'Radamsa'
        self.assertTrue(testMutatorConfig(config, testForInputFiles=False))
        mutatorInterface = MutatorInterface(config)

        corpusData = testutils.getCorpusData(
            config,
            networkData=self._getNetworkData(config))
        fuzzedCorpusData = mutatorInterface.fuzz(corpusData)

        # note that we only have one cli message, which is at index 0
        self.assertNotEqual(corpusData.networkData.messages[0]['data'],
                            fuzzedCorpusData.networkData.messages[0]['data'])


if __name__ == '__main__':
    unittest.main()
