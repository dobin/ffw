#!/usr/bin/python

import socket


def testServerConnection(config, targetPort):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', targetPort)

    try:
        sock.connect(server_address)
    except socket.error, exc:
        # server down
        return False

    sock.close()

    return True


# has to return False on error
# so crash can be detected
def sendDataToServerRaw(config, fuzzIterConfig):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', config["target_port"])

    try:
        sock.connect(server_address)
    except socket.error, exc:
        # server down
        return False

    if config["sendInitialDataFunction"] is not None:
        res = config["sendInitialDataFunction"](sock)
        # could not send, so already crash?
        if not res:
            return False

    # sock.setblocking(0)
    try:
        sock.sendall(fuzzIterConfig["data"])
    except socket.error, exc:
        return False

    if config["response_analysis"]:
        sock.settimeout(0.1)
        try:
            r = sock.recv(1024)
            # print "Received len: " + str(len(r))
        except Exception,e:
            #print "Recv exception"
            pass

    sock.close()

    return True


def sendDataToServerInterceptor(config, fuzzIterConfig):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', config["target_port"])

    try:
        sock.connect(server_address)
    except socket.error, exc:
        # server down
        return False

    # send all previous messages
    for message in config["_inputs"]:
        if message["from"] != "cli":
            continue

        if message == fuzzIterConfig["current_choice"]:
            break

        try:
            sock.sendall(message["data"])
        except socket.error, exc:
            return False

        # if config["receive_ansewrs"]:
            # if next msg is from server:
                #bla = sock.recv(1024)

    try:
        sock.sendall(fuzzIterConfig["data"])
    except socket.error, exc:
        return False

    # TODO: send the rest

    if config["response_analysis"]:
        sock.settimeout(0.1)
        try:
            r = sock.recv(1024)
            # print "Received len: " + str(len(r))
        except Exception,e:
            #print "Recv exception"
            pass

    sock.close()

    return True
