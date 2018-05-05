#!/usr/bin/env python2

import socket
import threading
import select
import logging
import os

from target.servermanager import ServerManager
from network import networkmanager
from common.corpusdata import CorpusData
from common.networkdata import NetworkData

"""
Interceptor

it perform a man-in-the-middle attack
the client has to connect to the specific port of this tool
all data will be forwarded to the server, and vice-versa

interceptor will also record all transmitted data, split up between
read()'s, and split between server and client

It will store the data in files with the name data_<connid>.pickle,
serialized python objects as pickle

This can be used later to fuzz server (or client) with ffw interceptor mode,
which excpects pickle file recorded here.

A recorded connection can be replayed to test it.
"""


# based on: https://gist.github.com/sivachandran/1969859 (no license)
class ClientTcpThread(threading.Thread):
    def createDataEntry(self, frm, data, index):
        return NetworkData.createNetworkMessage(frm, data, index)


    def __init__(self, config, clientSocket, targetHost, targetPort, threadId):
        threading.Thread.__init__(self)
        self.config = config
        self.__clientSocket = clientSocket
        self.__targetHost = targetHost
        self.__targetPort = targetPort
        self.__threadId = threadId
        self.data = []


    def run(self):
        logging.info("Client Thread" + str(self.__threadId) + " started")

        self.__clientSocket.setblocking(0)

        logging.info('Logging into: %s:%i' % (self.__targetHost, self.__targetPort) )
        targetHostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            targetHostSocket.connect((self.__targetHost, self.__targetPort))
        except Exception as e:
            logging.error("connect() exception: " + str(e))
            logging.error("  while connecting to: " + self.__targetHost + ":" + str(self.__targetPort))
            return
        targetHostSocket.setblocking(0)

        clientData = ""
        targetHostData = ""
        terminate = False
        n = 0
        while not terminate:
            inputs = [self.__clientSocket, targetHostSocket]
            outputs = []

            if len(clientData) > 0:
                outputs.append(self.__clientSocket)

            if len(targetHostData) > 0:
                outputs.append(targetHostSocket)

            try:
                inputsReady, outputsReady, errorsReady = select.select(inputs, outputs, [], 1.0)
            except Exception as e:
                logging.error(str(e))
                break

            for inp in inputsReady:
                if inp == self.__clientSocket:
                    try:
                        data = self.__clientSocket.recv(4096)
                    except Exception as e:
                        logging.error(str(e))

                    if data is not None:
                        if len(data) > 0:
                            logging.info("Received from client: " + str(self.__threadId) + ": " + str(len(data)))
                            targetHostData += data
                            self.data.append( self.createDataEntry("cli", data, n) )
                            n += 1
                        else:
                            terminate = True
                elif inp == targetHostSocket:
                    data = None
                    try:
                        data = targetHostSocket.recv(4096)
                        logging.info("target: recv data")
                    except Exception as e:
                        logging.error("target recv Exception: " + str(e))
                        break

                    if data is not None:
                        if len(data) > 0:
                            logging.info("Received from server: " + str(self.__threadId) + ": " + str(len(data)))
                            clientData += data
                            self.data.append( self.createDataEntry("srv", data, n) )
                            n += 1
                        else:
                            terminate = True

            for out in outputsReady:
                if out == self.__clientSocket and len(clientData) > 0:
                    bytesWritten = self.__clientSocket.send(clientData)
                    if bytesWritten > 0:
                        clientData = clientData[bytesWritten:]
                elif out == targetHostSocket and len(targetHostData) > 0:
                    bytesWritten = targetHostSocket.send(targetHostData)
                    if bytesWritten > 0:
                        targetHostData = targetHostData[bytesWritten:]

        self.__clientSocket.close()
        targetHostSocket.close()
        logging.info("ClientTcpThread terminating")

        # store all the stuff
        logging.info("Got " + str(len(self.data)) + " packets")
        fileName = self.getDataFilename()

        logging.info("Storing into file: " + fileName)
        networkData = NetworkData(self.config, self.data)
        corpusData = CorpusData(self.config, fileName, networkData)
        corpusData.writeToFile()


    def getDataFilename(self):
        n = 0
        filename = "data_" + str(n) + ".pickle"
        while os.path.isfile(filename):
            n += 1
            filename = "data_" + str(n) + ".pickle"

        return filename


class Interceptor(object):
    def __init__(self, config, onlyOne=False):
        self.config = config
        self.terminateAll = False
        self.onlyOne = onlyOne


    def _performTcpIntercept(self, localHost, localPort, targetHost, targetPort):
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            serverSocket.bind((localHost, int(localPort)))
            serverSocket.listen(5)
        except Exception as e:
            logging.error("Error binding to: %s:%s: %s" % (localHost, localPort, str(e)))
            return

        logging.info("Forwarding everything to %s:%s" % (targetHost, targetPort))
        logging.info("Waiting for new client on port: " + str(localPort))

        threadId = 0
        while True:
            try:
                clientSocket, address = serverSocket.accept()
                print("Got new client")
            except socket.error as e:
                logging.error("accept() Socket Error: " + str(e))
                logging.error("Try waiting a bit...")

                break
            except KeyboardInterrupt:
                logging.info("\nTerminating all clients...")
                self.terminateAll = True
                break

            ClientTcpThread(self.config, clientSocket, targetHost, targetPort, threadId).start()
            threadId += 1

            if self.onlyOne:
                break

        serverSocket.close()


    def _performUdpIntercept(self, localHost, localPort, targetHost, targetPort):
        dataArr = []
        n = 0

        # connect to server
        sockTarget = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # listening
        sockListen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logging.info("Listening on: " + str(localHost) + " : " + str(localPort))
        sockListen.bind((localHost, int(localPort)))
        sockTarget.settimeout(1.0)
        sockListen.settimeout(1.0)

        while True:
            try:
                try:
                    # wait for client msg
                    logging.info("Waiting for client msg...")
                    data, addrCli = sockListen.recvfrom(1024)  # buffer size is 1024 bytes
                    logging.info("cli: received message len: ", str(len(data)))
                    logging.info("     from: " + str(addrCli))
                    sockTarget.sendto(data, (targetHost, targetPort))

                    dataArr.append(self.createDataEntry('cli', data, n) )
                    n += 1
                except socket.timeout:
                    logging.warn("cli: recv() timeout from server, continuing...")

                # check if server sends answer
                try:
                    data, addrSrv = sockTarget.recvfrom(1024)
                    if data is not None:
                        logging.info("srv: Received from server: len: " + str(len(data)))
                        dataArr.append( self.createDataEntry('srv', data, n))

                        logging.info("     Forward data from server to: " + str(addrCli))
                        sockListen.sendto(data, addrCli)

                        n += 1
                except socket.timeout:
                    logging.warn("srv: recv() timeout from server, continuing...")

            except KeyboardInterrupt:
                logging.info("\nTerminating...")
                break

        # store all the stuff
        print("Got " + str(len(dataArr)) + " packets")
        fileName = "data_0.pickle"
        networkData = NetworkData(self.config, dataArr)
        corpusData = CorpusData(self.config, fileName, networkData)
        corpusData.writeToFile()


    # called from ffw
    def doIntercept(self, interceptorPort, targetPort):
        localHost = "0.0.0.0"
        targetHost = "localhost"

        self.config["target_port"] = targetPort

        # run the targetserver, as configured in config
        serverManager = ServerManager(self.config, 0, targetPort)
        isStarted = serverManager.start()
        if not isStarted:
            logging.error("Could not start server, check its output")
            return

        # test connection
        networkManager = networkmanager.NetworkManager(self.config, targetPort)

        if not networkManager.debugServerConnection():
            return

        # start mitm server
        if self.config["ipproto"] is "tcp":
            self._performTcpIntercept(localHost, interceptorPort, targetHost, targetPort)
        else:
            self._performUdpIntercept(localHost, interceptorPort, targetHost, targetPort)
