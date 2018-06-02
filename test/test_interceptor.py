#!/usr/bin/env python

import logging
import unittest
import os
import threading
import time

from common.corpusdata import CorpusData
from network.interceptor import Interceptor
from interceptorclientmockup import MockupClient
import testutils


class InterceptorTest(unittest.TestCase):
    def _getConfig(self):
        config = {
            "input_dir": "/tmp/ffw-test/in/",
            "temp_dir": "/tmp/ffw-test/temp/",

            "basedir": os.path.dirname(os.path.realpath(__file__)),
            "projdir": os.path.dirname(os.path.realpath(__file__)) + "/test",
            "target_port": 20000,
            "target_bin": os.path.dirname(os.path.realpath(__file__)) + "/interceptorservermockup.py",
            "target_dir": os.path.dirname(os.path.realpath(__file__)),
            "target_args": "%(port)i",
            "ipproto": "tcp",
            "recvTimeout": 0.1,
            "connectTimeout": 0.2,
        }
        return config


    def test_tcpintercept(self):
        logging.basicConfig(level=logging.DEBUG)
        config = self._getConfig()
        testutils.prepareFs(config)
        targetPort = 10001

        mockupClient = MockupClient(targetPort)
        interceptor = Interceptor(config, onlyOne=True)

        # start interceptor in background
        interceptorThread = threading.Thread(
            target=interceptor.doIntercept,
            args=(targetPort, config["target_port"]))
        interceptorThread.start()
        time.sleep(1)

        self.assertTrue(interceptorThread.isAlive())

        # gife time to bind
        time.sleep(1)

        # start client in background
        clientThread = threading.Thread(
            target=mockupClient.startClient,
            args=()
        )
        clientThread.start()

        # wait for all of them to finish
        while True:
            time.sleep(0.1)
            if not clientThread.isAlive() and not interceptorThread.isAlive():
                break

        # check if we got teh data
        filename = config["input_dir"] + "intercept0.pickle"
        corpusData = CorpusData(config, filename)
        corpusData.readFromFile()

        self.assertEqual(corpusData.networkData.messages[0]['data'], 'msg1')
        self.assertEqual(corpusData.networkData.messages[0]['from'], 'cli')

        self.assertEqual(corpusData.networkData.messages[1]['data'], 'msg2')
        self.assertEqual(corpusData.networkData.messages[1]['from'], 'srv')


if __name__ == '__main__':
    unittest.main()
