#!/usr/bin/python 

import socket


def testServerConnection(config):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', config["target_port"])

    try: 
        sock.connect(server_address)
    except socket.error, exc:
        # server down
        return False
    
    sock.close()

    return True


# has to return False on error
# so crash can be detected
def sendDataToServer(config, file):
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
    file = open(file, "r")
    data = file.read()

    try: 
        sock.sendall(data)
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

    file.close()
    sock.close()

    return True
