#!/usr/bin/env python2

import logging
import sys

from target.servermanager import ServerManager
from . import networkmanager
from common.corpusmanager import CorpusManager


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


    def test(self):
        targetPort = self.config["target_port"]
        serverManager = ServerManager(self.config, 0, targetPort, hideChildOutput=False)
        networkManager = networkmanager.NetworkManager(self.config, targetPort)
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


        for corpusData in corpusManager:
            print "Testing new CorpusData"
            self.stats = {}
            n = 0
            while n < len(corpusData.networkData.messages):
                self.stats[n] = 0
                n += 1

            it = 0
            while it < 3:
                print("==== Iteration =====")
                networkManager.openConnection()
                self.sendMessages(networkManager, corpusData.networkData)
                networkManager.closeConnection()
                it += 1

            print("Itercount: " + str(it))
            print("Fails:")
            if len(self.stats) == 0:
                print("None :-)")
            else:
                for key, value in self.stats.items():
                    print("Fails at msg #" + str(key) + ": " + str(value))

        serverManager.stop()


    def sendMessages(self, networkManager, networkData):
        n = 0
        for message in networkData.messages:
            if self.config["maxmsg"] and message["index"] > self.config["maxmsg"]:
                break

            sys.stdout.write("Handling msg: " + str(n) + " ")
            if message["from"] == "srv":
                print("Receiving...")
                print("  Orig: " + str(len(message["data"])))
                ret = networkManager.receiveData(message)

                if not ret:
                    print("  Could not receive")
                    self.stats[n] += 1
                else:
                    print("  Real: " + str(len(ret)))
                    if len(message["data"]) != len(ret):
                        self.stats[n] += 1

            if message["from"] == "cli":
                print("Sending...")
                print("  Send: " + str(len(message["data"])))
                ret = networkManager.sendData(message)
                if not ret:
                    logging.debug("  server not reachable")
                    self.stats[n] += 1

            n += 1
