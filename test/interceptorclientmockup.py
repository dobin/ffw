#!/usr/bin/env python

import socket
import logging
import sys


class MockupClient(object):
    def __init__(self, targetPort):
        self.sock = None
        self.targetPort = targetPort


    def startClient(self):
        logging.info("Client: Connect to: " + str(self.targetPort))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', int(self.targetPort))

        try:
            self.sock.connect(server_address)
        except socket.error as exc:
            logging.error("Client: Connect error: " + str(exc))
            return False

        self.sendData()
        self.sock.close()

        return True


    def sendData(self):
        self.sock.send("msg1")

        msg2 = self.sock.recv(1024)
        logging.info("Client: Received: " + msg2)


def main():
    mockupClient = MockupClient(sys.argv[1])
    mockupClient.startClient()


if __name__ == "__main__":
    main()
