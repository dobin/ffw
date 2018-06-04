#!/usr/bin/env python2

import logging
import utils

from target.servermanager import ServerManager
from . import networkmanager
from common.corpusmanager import CorpusManager

messageHaveTimeouts = """
We have timeouts. This means that we closed the connection, because the server
didnt answer fast enough, or for other reasons.
You can try to increase the timeout to a sane level, but this usually means
that the server has some kinde of processing/ratelimiting/antiddos/resolving
stuff to do. Try to patch it.

Alternatively, increase receive timeout in config.py:
  \"recvTimeout\": 0.1,
or even:
  \"recvTimeout\": 4,

Also enable server output via:
  \"hideTargetStdout\": False,
"""


class Tester():
    """
    Test (recorded) data.

    If we recorded data, e.g. by using interceptor, we should test
    if we can replay it correctly. And the server answers us correctly.
    If we have a fail after a certain amount of messages, we need to
    maybe authenticate, or add a cookie. This has to be implemented
    in dedicated proto classes.

    If all messages are replayed without issue, we have the perfect
    fuzzing target.
    """

    def __init__(self, config):
        self.config = config
        self.stats = None
        self.networkManager = None
        self.iterCount = 32


    def test(self):
        targetPort = self.config["target_port"]
        serverManager = ServerManager(
            self.config,
            0,
            targetPort,
            hideChildOutput=self.config['hideTargetStdout'])
        networkManager = networkmanager.NetworkManager(self.config, targetPort)
        self.networkManager = networkManager
        corpusManager = CorpusManager(self.config)
        corpusManager.loadCorpusFiles()

        print("Using port: " + str(targetPort))
        serverManager.start()

        if not networkManager.debugServerConnection():
            print("Could not connect. Are you sure you have the right port?")
            serverManager.stop()
            return
        else:
            print("Initial test successful - could connect to server.")

        if corpusManager.getCorpusCount() == 0:
            print("No input corpus found - nothing to test. Exiting.")

        for corpusData in corpusManager:
            self.testCorpus(corpusData)

        serverManager.stop()


    def testCorpus(self, corpusData):
        print "---[ Testing CorpusData: " + corpusData.filename + " " + str(self.iterCount) + " times"
        print("We use the following recvTimeout: " + str(self.config['recvTimeout']))
        it = 0
        corpusArr = []
        while it < self.iterCount:
            corpusDataNew = corpusData.createFuzzChild("1")
            self.networkManager.sendAllData(corpusDataNew, recordAnswer=True)
            corpusArr.append(corpusDataNew)
            it += 1

        hasTimeouts = False
        for idx, message in enumerate(corpusData.networkData.messages):
            if message['timeouts'] > 0:
                hasTimeouts = True
                print("Message %d timeouts: %d (out of %d)"
                      % ( message['index'], message['timeouts'], self.iterCount))

                print("Latencies:")
                print(str(corpusData))

                if message['timeouts'] == self.iterCount:
                    print("Corpus is fully unrealiable.")
                else:
                    print("Corpus is partially unreliable.")

                print("")

                n = self.getClientAnswerBefore(idx, corpusData.networkData)
                print("Last request before good answer: " + str(n))
                utils.hexdumpc( corpusDataNew.networkData.messages[n]['data'] )

                n = self.getServerAnswerBefore(idx, corpusData.networkData)
                print("Last good server answer was: " + str(n))
                utils.hexdumpc( corpusDataNew.networkData.messages[n]['data'] )

                print("Msg before request: " + str(idx - 1))
                utils.hexdumpc( corpusDataNew.networkData.messages[idx - 1]['data'] )


        if hasTimeouts:
            print(messageHaveTimeouts)
        else:
            print("No timeouts, looking fine!")


    def getClientAnswerBefore(self, idx, networkData):
        n = self.getServerAnswerBefore(idx, networkData)
        while networkData.messages[n]['from'] != 'cli':
            n -= 1

            # no underflow pls
            if n < 0:
                return 0

        return n


    def getServerAnswerBefore(self, idx, networkData):
        n = idx - 1
        while networkData.messages[n]['from'] != 'srv':
            n -= 1

            # no underflow pls
            if n < 0:
                return 0

        return n
