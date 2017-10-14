#!/usr/bin/env python2

import socket
import logging
import time
import sys


class NetworkManager(object):
    """
        Opens a network connection to the server
    """
    def __init__(self, config, targetPort):
        self.config = config
        self.sock = None
        self.targetPort = int(targetPort)

        if config["ipproto"] is "tcp":
            logging.info("Using: TCP")
            self.openConnection = self.openConnectionTcp
            self.closeConnection = self.closeConnectionTcp
            self.sendData = self.sendDataTcp
            self.receiveData = self.receiveDataTcp
            self.testServerConnection = self.testServerConnectionTcp
        else:
            logging.info("Using: UDP")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(1.0)
            self.openConnection = self.openConnectionUdp
            self.closeConnection = self.closeConnectionUdp
            self.sendData = self.sendDataUdp
            self.receiveData = self.receiveDataUdp
            self.testServerConnection = self.testServerConnectionUdp

    ######################################33

    def openConnectionTcp(self):
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


    def closeConnectionTcp(self):
        if self.sock is not None:
            self.sock.close()


    def sendDataTcp(self, message=None):
        """Send data to the server."""
        if self.sock is None:
            logging.error("Trying to send to a closed socket")
            sys.exit(1)

        try:
            if self.config["protoObj"] is not None and message is not None:
                message["data"] = self.config["protoObj"].onPreSend(message["data"], message["index"])

            self.sock.sendall(message["data"])
        except socket.error, exc:
            logging.debug("  sendData(): Send data exception on msg " + str(message["index"]) + ": " + str(exc))
            return False

        return True


    def receiveDataTcp(self, message=None):
        """Receive data from the server."""
        self.sock.settimeout(0.1)
        try:
            data = self.sock.recv(1024)
            if self.config["protoObj"] is not None and message is not None:
                self.config["protoObj"].onPostRecv(data, message["index"])
            return data
        except Exception, e:
            logging.info("ReceiveData err on msg " + str(message["index"]) + ": " + str(e))
            return None


    def testServerConnectionTcp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', self.targetPort)

        try:
            sock.connect(server_address)
        except socket.error, exc:
            return False

        sock.close()

        return True

    ######################################33

    def openConnectionUdp(self):
        #self.closeConnection()

        return self.testServerConnection()

#        dest = ('127.0.0.1', self.targetPort)

#        try:
#            self.sock.sendto("PING", dest)
#        except Exception as e:
#            print "E: " + str(e)
#            return False
#
#        return True

#        result = self.sock.connect_ex(dest)
#        if result == 0:
#            return True
#        else:
#            return False


    def closeConnectionUdp(self):
        #print "Close"
        #self.sock.close()
        pass


    def sendDataUdp(self, message=None):
        """Send data to the server."""
        if self.sock is None:
            logging.error("Trying to send to a closed socket")
            sys.exit(1)

        try:
            if self.config["protoObj"] is not None and message is not None:
                message["data"] = self.config["protoObj"].onPreSend(message["data"], message["index"])

            self.sock.sendto(message["data"], ('127.0.0.1', self.targetPort))
        except socket.error, exc:
            logging.debug("  sendData(): Send data exception on msg " + str(message["index"]) + ": " + str(exc))
            return False

        return True


    def receiveDataUdp(self, message=None):
        """Receive data from the server."""
        try:
            data, addr = self.sock.recvfrom(1024)
            if self.config["protoObj"] is not None and message is not None:
                self.config["protoObj"].onPostRecv(data, message["index"])
            return data
        except Exception, e:
            logging.info("ReceiveData err on msg " + str(message["index"]) + ": " + str(e))
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
            logging.info("testServerConnection1: Server DOWN! " + str(e))
            return False


    ######################################33
    # Non-proto specific

    def sendMessages(self, msgArr):
        if not self.openConnection():
            return False

        for message in msgArr:
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
            if n > 10:
                logging.error("Server not ready after 10 tries.. still continuing")
            time.sleep(0.2)
            n += 1

        logging.info("Server is ready (accepting connections)")
        return True
