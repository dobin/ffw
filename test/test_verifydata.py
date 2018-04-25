#!/usr/bin/env python

import unittest
import time

from common.networkdata import NetworkData
from common.corpusdata import CorpusData
from common.crashdata import CrashData
from common.verifydata import VerifyData
import testutils


class VerifyDataTest(unittest.TestCase):
    def _getConfig(self):
        config = {
            "input_dir": "/tmp/ffw-test/in",
            "outcome_dir": "/tmp/ffw-test/out",
            "verified_dir": "/tmp/ffw-test/verified",
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


    def _getCrashData(self, config):
        corpusData = self._getCorpusData(config)
        crashData = CrashData(config, corpusData, '-')
        crashData.setCrashInformation(asanOutput="meh")
        return crashData


    def _getVerifyData(self, config):
        crashData = self._getCrashData(config)
        verifyData = VerifyData(config, crashData, faultaddress=1337)
        return verifyData


    def test_writeread(self):
        config = self._getConfig()
        testutils.prepareFs(config)

        # get some example verifyData
        verifyData = self._getVerifyData(config)

        # write it
        verifyData.writeToFile()

        # try to read it again
        verifyData2 = VerifyData(config, filename=verifyData.filename)
        verifyData2.readFromFile()

        # test an example of each layer
        self.assertEqual(
            verifyData.faultaddress,
            verifyData2.faultaddress
        )
        self.assertEqual(
            verifyData.crashData.asanOutput,
            verifyData2.crashData.asanOutput)
        self.assertEqual(
            verifyData.crashData.corpusData.seed,
            verifyData2.crashData.corpusData.seed)
        self.assertEqual(
            verifyData.crashData.corpusData.networkData.messages[0]['data'],
            verifyData2.crashData.corpusData.networkData.messages[0]['data'],
        )


if __name__ == '__main__':
    unittest.main()
