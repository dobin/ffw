#!/usr/bin/env python

# a simple program which tries to bind to port 1234
# exit code 1 if fail

import socket
import logging
import time
import os

try:
    sockRed = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    arg = ('localhost', 1234)
    sockRed.bind( arg )
    sockRed.listen(5)
    print(str(os.getpid()) + ": Sleep for 1: " + str(arg))
    time.sleep(1)
    print("Finish")
    sockRed.close()
    exit(0)
except Exception as e:
    logging.error("Could not bind: " + str(e))
    exit(1)
