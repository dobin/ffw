#!/usr/bin/env python

# a simple program which tries to bind to port 1234
# exit code 1 if fail

import socket
import logging

try:
    sockRed = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockRed.bind( ('localhost', 1234) )
    sockRed.listen(5)

    sockRed.close()
    exit(0)
except Exception as e:
    logging.error("Could not bind: " + str(e))
    exit(1)
