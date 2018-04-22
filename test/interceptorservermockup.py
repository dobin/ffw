#!/usr/bin/env python

import socket
import logging
import sys


class MockupServer(object):
    def __init__(self, basePort):
        self.sock = None
        self.basePort = basePort


    def startServer(self):
        logging.info("Server: Listen on: " + str(self.basePort))

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.socket.bind(("localhost", int(self.basePort)))
        except socket.error as msg:
            logging.error('Server: Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])

        self.socket.listen(10)

        self.loop()


    def loop(self):
        while(True):
            conn, addr = self.socket.accept()

            msg1 = conn.recv(1024)
            logging.info("Server: Received: " + msg1)
            conn.send("msg2")


    def sendData(self):
        self.sock.send("msg1")


def main():
    mockupServer = MockupServer(sys.argv[1])
    mockupServer.startServer()


if __name__ == "__main__":
    main()
