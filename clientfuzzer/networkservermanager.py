
import socket
import sys
import logging


class NetworkServerManager(object):
    print "Network Server Manager"

    def __init__(self, config, targetPort):
        self.config = config
        self.targetPort = targetPort
        self.data = None
        self.sock = None

    def start(self):
        self._startListen()
        print "Start Server Manager"


    def setFuzzData(self, data):
        self.fuzzingIterationData = data
        print "Set data"


    def handleConnection(self):
        print "Waiting for connection..."
        conn, addr = self.socket.accept()

        print "Client connected!"

        print "recv..."
        buf = conn.recv(1024)
        print "  Received: " + buf

        print "send..."
        conn.send("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")

        print "finished"
        conn.close()


    def _startListen(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print 'Socket created'

        #Bind socket to local host and port
        try:
            self.socket.bind(("localhost", self.targetPort))
        except socket.error as msg:
            print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()

        print 'Socket bind complete'

        #Start listening on socket
        self.socket.listen(10)
        print 'Socket now listening'
