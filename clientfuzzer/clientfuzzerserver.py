#!/usr/bin/env python

import socket
import sys
import logging


class ClientFuzzerServer(object):
    def __init__(self, config, targetPort):
        self.config = config
        self.targetPort = targetPort
        self.data = None
        self.sock = None

    def start(self):
        print "Start Server Manager"
        return self._startListen()


    def setFuzzData(self, data):
        self.fuzzingIterationData = data
        print "Set data"


    def handleConnection(self):
        print "Waiting for connection..."
        conn, addr = self.socket.accept()

        print "Client connected!"

        for message in self.fuzzingIterationData.fuzzedData:
            if self.config["maxmsg"] and message["index"] > self.config["maxmsg"]:
                break

            if message["from"] == "srv":
                print ".. send"
                if not self._sendData(conn, message):
                    break
            else:
                print ".. recv"
                if not self._receiveData(conn, message):
                    break

        print "finished"
        conn.close()


    def _receiveData(self, conn, message):
        return conn.recv(1024)

    def _sendData(self, conn, message):
        conn.send(message["data"])

    def _startListen(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print 'Socket created'

        #Bind socket to local host and port
        try:
            self.socket.bind(("localhost", self.targetPort))
        except socket.error as msg:
            print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            return False

        print 'Socket bind complete'

        #Start listening on socket
        self.socket.listen(10)
        print 'Socket now listening'

        return True
