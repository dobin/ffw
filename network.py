#!/usr/bin/python

import socket

# used by both, ServerManager and DebugServerManager
def testServerConnection(targetPort):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', targetPort)

    try:
        sock.connect(server_address)
    except socket.error, exc:
        # server down
        return False

    sock.close()

    return True
