#!/usr/bin/env python2

import socket
import logging
import time


class NetworkManager(object):
    """
        Opens a network connection to the server
    """
    def __init__(self, config, targetPort):
        self.config = config
        self.sock = None
        self.targetPort = int(targetPort)


    def openConnection(self):
        """
        Opens a TCP connection to the server
        True if successful
        False if not (server down)

        Note: This is also used to test if the server
        has crashed
        """
        self.closeConnection()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', self.targetPort)
        logging.info("Open connection on localhost:" + str(self.targetPort))
        try:
            self.sock.connect(server_address)
        except socket.error, exc:
            # server down
            self.sock.close()
            logging.info("  Could not connect! Server is down.")
            return False

        return True


    def closeConnection(self):
        if self.sock is not None:
            self.sock.close()


    def sendData(self, message):
        """Send data to the server"""
        try:
            logging.debug("  Send msg " + str(message["index"]))
            logging.debug("    to server. len: " + str(len(message["data"])))
            if self.config["protoObj"] != None:
                message["data"] = self.config["protoObj"].onPreSend(message["data"], message["index"])
            self.sock.sendall(message["data"])
        except socket.error, exc:
            logging.debug("  sendData(): Send data exception: " + str(exc))
            return False

        return True


    def receiveData(self, message):
        """Receive data from the server"""
        self.sock.settimeout(0.1)
        try:
            data = self.sock.recv(1024)
            if self.config["protoObj"] != None:
                self.config["protoObj"].onPostRecv(data, message["index"])
            print "  Received for msg " + message["index"] + ": " + str(len(data))
            return data
        except Exception, e:
            logging.info("ReceiveData err")
            return None



    def sendMessages(self, msgArr):
        if not self.openConnection():
            return False

        for message in msgArr:
            if message["from"] != "cli":
                continue

            logging.info("Send message")
            self.sendData(message["data"])

        self.closeConnection()
        return True


    def waitForServerReadyness(self):
        while not self.testServerConnection():
            print "Server not ready, waiting and retrying"
            time.sleep(0.2)  # wait a bit till server is ready


    def testServerConnection(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', self.targetPort)

        try:
            sock.connect(server_address)
        except socket.error, exc:
            # server down
            logging.info("testServerConnection: Server is DOWN")
            return False

        sock.close()

        return True
