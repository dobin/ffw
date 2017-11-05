import socket
import sys
import time


class HonggComm(object):
    def __init__(self):
        print("Init")
        self.sock = None


    def openSocket(self, fuzzerPid):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        server_address = '/tmp/honggfuzz_socket.' + str(fuzzerPid)
        print(( 'connecting to %s' % server_address))

        while True:
            try:
                sock.connect(server_address)
                break
            except socket.error as msg:
                print(("A: " + str(msg)))
                #sys.exit(1)
                time.sleep(0.2)

        print ("connected!")
        self.sock = sock

    def readSocket(self):
        recv = self.sock.recv(4).decode()
        return recv

    def writeSocket(self, data):
        self.sock.sendall( str.encode(data) )

    def closeSocket(self):
        self.sock.close()
