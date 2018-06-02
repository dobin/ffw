#!/usr/bin/env python

import unittest
import os

from common.corpusdata import CorpusData
from common.networkdata import NetworkData
from mutator.mutatorinterface import MutatorInterface, testMutatorConfig
import testutils

from mutator.mutator_dictionary import MutatorDictionary


class DictionaryFuzzerTest(unittest.TestCase):
    def _getConfig(self):
        config = {
            "target_dir": "/tmp/ffw-test/bin",
            "input_dir": "/tmp/ffw-test/in",
            "temp_dir": "/tmp/ffw-test/temp",
            "basedir": os.path.dirname(os.path.realpath(__file__)) + "/..",
            "processes": 1,
        }

        return config


    def _getNetworkData(self, config):
        networkMessages = [
            {
                'data': 'msg 1 cli test1',
                'from': 'cli',
                'index': 0,
            },
            {
                'data': 'msg 1 cli test1 test2 test2',
                'from': 'cli',
                'index': 1,
            },
        ]

        networkData = NetworkData(config,
                                  networkMessages)
        return networkData


    def _getCorpusData(self, config):
        networkData = self._getNetworkData(config)
        corpusData = CorpusData(config, 'data0', networkData)
        return corpusData


    def _writeDictionary(self, config):
        with open(config['target_dir'] + '/dictionary.txt', "w") as f:
            f.write("test1\n")
            f.write("test2\n")


    def test_dictionaryfuzzer(self):
        config = self._getConfig()
        testutils.prepareFs(config)
        config['mutator'] = [ 'Dictionary' ]
        self._writeDictionary(config)
        self.assertTrue(testMutatorConfig(config, 'basic'))
        mutatorInterface = MutatorInterface(config, 0)

        corpusData = self._getCorpusData(config)

        fuzzedCorpusData1 = mutatorInterface.fuzz(corpusData)
        fuzzedCorpusData2 = mutatorInterface.fuzz(corpusData)
        fuzzedCorpusData3 = mutatorInterface.fuzz(corpusData)
        fuzzedCorpusData4 = mutatorInterface.fuzz(corpusData)
        fuzzedCorpusData5 = mutatorInterface.fuzz(corpusData)

        #print("1: " + fuzzedCorpusData1.networkData.messages[0]['data'])
        self.assertEqual(
            fuzzedCorpusData1.networkData.messages[0]['data'],
            'msg 1 cli test2'
        )
        self.assertIsNotNone(
            fuzzedCorpusData1.networkData.fuzzMsgIdx
        )
        self.assertIsNotNone(
            fuzzedCorpusData1.networkData.fuzzMsgChoice
        )
        self.assertEqual(
            fuzzedCorpusData2.networkData.messages[1]['data'],
            'msg 1 cli test2 test2 test2'
        )
        self.assertEqual(
            fuzzedCorpusData3.networkData.messages[1]['data'],
            'msg 1 cli test1 test1 test2'
        )
        self.assertEqual(
            fuzzedCorpusData4.networkData.messages[1]['data'],
            'msg 1 cli test1 test2 test1'
        )
        self.assertIsNone(
            fuzzedCorpusData5
        )


    def test_dictionaryfuzzerWithRadamsa(self):
        config = self._getConfig()
        testutils.prepareFs(config)
        config['mutator'] = [ 'Dictionary', 'Radamsa' ]
        self._writeDictionary(config)
        self.assertTrue(testMutatorConfig(config, 'basic'))
        mutatorInterface = MutatorInterface(config, 0)

        corpusData = self._getCorpusData(config)

        n = 0
        stats = {
            'Dictionary': 0,
            'Radamsa': 0,
        }
        while n < 20:
            fuzzedCorpusData = mutatorInterface.fuzz(corpusData)
            stats[ fuzzedCorpusData.fuzzer ] += 1
            n += 1

        self.assertEqual(stats['Dictionary'], 4)
        self.assertEqual(stats['Radamsa'], 16)


if __name__ == '__main__':
    unittest.main()
