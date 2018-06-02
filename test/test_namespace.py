#!/usr/bin/env python2

import subprocess
import socket
import time

import unittest
from target import targetutils


class TestLinuxNamespace(unittest.TestCase):
    def test_Namespaces(self):

        targetutils.startInNamespace(self.startProcess, 0)
        targetutils.startInNamespace(self.startProcess, 1)


    def startProcess(self):
        # start mockup server in background
        ret = subprocess.Popen(['./test/interceptorservermockup.py', "1234"])
        server_address = ('localhost', 1234)

        time.sleep(1)
        # target should be alive
        self.assertFalse(ret.poll())

        # try to connect to it
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            ret = self.sock.connect(server_address)
            self.sock.send("msg1")
            ret = self.sock.recv(4)
            self.assertEqual(ret, 'msg2')
        except socket.error as exc:
            self.assertFalse(True)


if __name__ == '__main__':
    unittest.main()
