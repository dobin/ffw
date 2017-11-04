#!/usr/bin/env python2

import sys
import socket

def main():
    if len(sys.argv) == 1:
        print("Usage: vulnserver_client.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    host = "127.0.0.1"

    print("Connecting to " + host + " port " + str(port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest = (host, port)
    sock.connect(dest)

    try:
        print("Send message 1")
        sock.send("AAAA")
        sock.recv(1024)

        print("Send message 2")
        sock.send("BBBB")
        sock.recv(1024)

        print("Send message 3")
        sock.send("CCCC")
        sock.recv(1024)

        sock.close()
    except Exception as e:
        print(("Server DOWN! " + str(e)))


if __name__ == '__main__':
    main()
