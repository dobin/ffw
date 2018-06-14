#!/usr/bin/env python2

import socket
import logging
import time
import sys
import os


class NetworkManager(object):
    """
        Opens a network connection to the server
    """
    def __init__(self, config, targetPort):
        self.config = config
        self.sock = None
        self.targetPort = int(targetPort)

        self.connectTimeout = config['connectTimeout']
        self.recvTimeout = config['recvTimeout']
        self.testServerConnectionTimeout = 1

        if config["ipproto"] is "tcp":
            logging.info("Using: TCP")
            self.openConnection = self.openConnectionTcp
            self.closeConnection = self.closeConnectionTcp
            self.sendData = self.sendDataTcp
            self.receiveData = self.receiveDataTcp
            self.testServerConnection = self.testServerConnectionTcp
        elif config["ipproto"] is "udp":
            logging.info("Using: UDP")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(1.0)
            self.openConnection = self.openConnectionUdp
            self.closeConnection = self.closeConnectionUdp
            self.sendData = self.sendDataUdp
            self.receiveData = self.receiveDataUdp
            self.testServerConnection = self.testServerConnectionUdp
        else:
            logging.error("Unknown proto: -" + config["ipproto"] + "-")


    ######################################


    def openConnectionTcp(self):
        """
        Opens a TCP connection to the server / targetself.

        True if successful
        False if not (server down)

        Note: This is also used to test if the server has crashed
        """
        self.closeConnection()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.connectTimeout)

        server_address = ('localhost', self.targetPort)
        logging.info("NET Open connection on localhost:" + str(self.targetPort))
        try:
            self.sock.connect(server_address)

            if "high_performance" in self.config:
                self.sock.setblocking(0)
        except socket.error as exc:
            # server down
            self.sock.close()
            logging.info("NET  Could not connect! Server is down: " + str(exc))
            self.sock = None
            return False

        return True


    def closeConnectionTcp(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None


    def sendDataTcp(self, message=None):
        """Send data to the server."""
        if self.sock is None:
            logging.error("NET Trying to send to a closed socket")
            sys.exit(1)

        try:
            logging.debug("Sending: " + message["data"])
            if self.config["protocolInstance"] is not None and message is not None:
                message["data"] = self.config["protocolInstance"].onPreSend(message["index"], message["data"])
            self.sock.sendall(message["data"])
        except socket.error as exc:
            logging.debug("NET  sendData(): Send data exception on msg " + str(message["index"]) + ": " + str(exc))
            return False

        return True


    def receiveDataTcp(self, message=None):
        """Receive data from the server."""
        self.sock.settimeout(self.recvTimeout)
        try:
            data = self.sock.recv(1024)
            logging.debug("Received: " + str(data))
            if self.config["protocolInstance"] is not None and message is not None:
                self.config["protocolInstance"].onPostRecv(data, message["index"])
            return data
        except Exception as e:
            logging.info("NET ReceiveData err on msg " + str(message["index"]) + ": " + str(e))
            return None


    def testServerConnectionTcp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', self.targetPort)
        logging.debug("NET testServerConnectionTcp: connect to " + str(server_address))
        sock.settimeout(self.testServerConnectionTimeout)
        try:
            sock.connect(server_address)
        except socket.error as exc:
            logging.info("NET Connection error: " + str(exc))
            sock.close()
            return False

        sock.close()

        return True

    ######################################33

    def openConnectionUdp(self):
        self.closeConnection()

        if not self.testServerConnection():
            return False

        logging.info("NET Open udp connection")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dest = ('127.0.0.1', self.targetPort)
        self.sock.connect(dest)

        # this mostly defines the speed of UDP based fuzzing
        self.sock.settimeout(0.1)

        return True


    def closeConnectionUdp(self):
        logging.info("NET Close udp connection")
        self.sock.close()


    def sendDataUdp(self, message=None):
        """Send data to the server."""
        if self.sock is None:
            logging.error("NET Trying to send to a closed socket")
            sys.exit(1)

        try:
            if self.config["protocolInstance"] is not None and message is not None:
                message["data"] = self.config["protocolInstance"].onPreSend(message["data"], message["index"])

            self.sock.sendto(message["data"], ('127.0.0.1', self.targetPort))
        except socket.error as exc:
            logging.debug("NET  sendData(): Send data exception on msg " + str(message["index"]) + ": " + str(exc))
            return False

        return True


    def receiveDataUdp(self, message=None):
        """Receive data from the server."""
        try:
            data, addr = self.sock.recvfrom(1024)
            if self.config["protocolInstance"] is not None and message is not None:
                self.config["protocolInstance"].onPostRecv(data, message["index"])
            return data
        except Exception as e:
            logging.info("NET ReceiveData err on msg " + str(message["index"]) + ": " + str(e))
            return None


    def testServerConnectionUdp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        dest = ('127.0.0.1', self.targetPort)
        logging.debug("testServerConnectionUdp: connect to " + str(dest))
        sock.connect(dest)

        try:
            sock.send("PING")
            sock.send("PING")  # yes, send it two times. once is not enough to create exception!
            sock.close()
            return True
        except Exception as e:
            logging.info("NET testServerConnection1: Server DOWN! " + str(e))
            return False


    ######################################33
    # Non-proto specific

    def debugServerConnection(self):
        n = 0
        alive = False
        while n < 10:
            logging.info("NET Check if we can connect to server localhost:" + str(self.targetPort))
            alive = self.testServerConnection()
            if alive:
                return True

            n += 1
            time.sleep(0.5)

        if not alive:
            logging.error("NET  Server not alive, aborting - " + str(self.targetPort))
            self._printErrAnalysis()
            print("")
            print("Common errors:")
            print("* Did you specify the correct port?")
            print("* Did you specify all necessary command line arguments for target (config file etc)?")
            print("* Are the paths/working-directory of target set correctly?")
            print("* In honggfuzz mode: Is the target compiled with hfuzz_cc compiler?")

        return False


    def _printErrAnalysis(self):
        binaryName = os.path.basename(self.config["target_bin"])

        cmdPs = "ps auxwww | grep %s" % (binaryName)
        print("Check if process exists: " + cmdPs)
        os.system(cmdPs)

        cmdNetstat = "lsof -i -P "
        print("Check if port is open: " + cmdNetstat)
        os.system(cmdNetstat)

        print("Trying netcat")
        cmdNc = "echo bla | nc -v localhost " + str(self.targetPort)
        os.system(cmdNc)

        print("List intefaces")
        cmdIp = "ip a l"
        os.system(cmdIp)


    def sendMessages(self, networkData):
        if not self.openConnection():
            return False

        for message in networkData.messages:
            if self.config["maxmsg"] and message["index"] > self.config["maxmsg"]:
                break

            if message["from"] == "srv":
                if not self.receiveData(message):
                    break
            else:
                if not self.sendData(message):
                    break

        self.closeConnection()
        return True


    def waitForServerReadyness(self):
        n = 0
        while not self.testServerConnection():
            logging.debug("NET Trying to connect")
            if n > 20:
                logging.error("NET WaitForServerReadyNess: Server no ready after 20 tries of 0.2s (4s).. aborting")
                self._printErrAnalysis()
                return False

            time.sleep(0.2)
            n += 1

        logging.info("NET Server is ready (accepting connections)")
        return True


    def sendAllData(self, corpusData, recordAnswer=False):
        logging.info("Send data: ")
        n = 0
        while not self.openConnection():
            time.sleep(0.2)
            n += 1
            if n > 6:
                self.closeConnection()
                return False

        if self.config["protocolInstance"] is not None:
            self.config["protocolInstance"].onNewIteration()

        beforeFuzzed = True
        for idx, message in enumerate(corpusData.networkData.messages):
            if 'isFuzzed' in message and message['isFuzzed']:
                beforeFuzzed = False

            if message["from"] == "srv":
                t1 = time.time()
                r = self.receiveData(message)
                t2 = time.time()

                # If we have a parent, this is a fuzzed message, so we add the
                # stats to the parent corpus.
                if not r:
                    if beforeFuzzed:
                        if corpusData._parent:
                            corpusData._parent.networkData.updateMessageTimeoutCount(idx)
                        else:
                            corpusData.networkData.updateMessageTimeoutCount(idx)

                    # fail fast
                    self.closeConnection()
                    return True
                else:
                    if corpusData._parent:
                        corpusData._parent.networkData.updateMessageLatency(idx, (t2 - t1))
                    else:
                        corpusData.networkData.updateMessageLatency(idx, (t2 - t1))
                    if recordAnswer:
                        message['data'] = r

            if message["from"] == "cli":
                logging.debug("  Sending message: " +
                              str(corpusData.networkData.messages.index(message)))
                res = self.sendData(message)
                if res is False:
                    self.closeConnection()
                    return True

        self.closeConnection()

        return True


    def sendPartialPreData(self, networkData):
        """For: BasicMode."""
        logging.info("NET Send pre data: ")

        for idx, message in enumerate(networkData.messages):
            if message == networkData.fuzzMsgChoice:
                break

            if message["from"] == "srv":
                t1 = time.time()
                r = self.receiveData(message)
                t2 = time.time()
                if not r:
                    networkData.updateMessageTimeoutCount(idx)
                    return False
                else:
                    networkData.updateMessageLatency(idx, (t2 - t1))

            if message["from"] == "cli":
                logging.debug("NET  Sending pre message: " + str(networkData.messages.index(message)))
                ret = self.sendData(message)
                if not ret:
                    return False

        return True


    def sendPartialPostData(self, networkData):
        """For: BasicMode."""
        logging.info("NET Send data: ")

        s = False
        for idx, message in enumerate(networkData.messages):
            # skip pre messages
            if message == networkData.fuzzMsgChoice:
                s = True

            if s:
                if message["from"] == "srv":
                    t1 = time.time()
                    r = self.receiveData(message)
                    t2 = time.time()
                    if not r:
                        networkData.updateMessageTimeoutCount(idx)
                        return False
                    else:
                        networkData.updateMessageLatency(idx, (t2 - t1))

                if message["from"] == "cli":
                    if "isFuzzed" in message:
                        logging.debug("NET   Sending fuzzed message: " + str(networkData.messages.index(message)))
                    else:
                        logging.debug("NET   Sending post message: " + str(networkData.messages.index(message)))
                    res = self.sendData(message)
                    if res is False:
                        return False

        return True


    def tuneTimeouts(self, maxLatency):
        newMaxLatency = round(maxLatency * 3, 3)
        origTimeout = self.recvTimeout

        if newMaxLatency != origTimeout:
            self.recvTimeout = newMaxLatency

            # min 20ms
            # we basically cannot get more than ~50/s
            if self.recvTimeout < 0.002:
                self.recvTimeout = 0.002

            # max 200ms (5/s)
            if self.recvTimeout > 0.2:
                self.recvTimeout = 0.2

            logging.info("Set recvTimeout to: " + str(self.recvTimeout) + "  orig was: " + str(origTimeout))
