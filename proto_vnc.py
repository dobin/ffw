#!/usr/bin/env python2

import hexdump
from Crypto.Cipher import DES
import struct


"""
0: recv: protocolversion
1: send: protocol (?)
2: recv: authentication
3:
"""


# copied from:
#   https://github.com/n00py/AngryHippo/blob/master/hippo.py
# no license
def handshake(key, chall):
    #https://tools.ietf.org/html/rfc6143#section-7.2.2
    #http://www.vidarholen.net/contents/junk/vnc.html
    #Truncate to 8 chars
    key = key[:8]
    # Convert to binary
    binary = (' '.join(format(ord(x), 'b') for x in key))
    binaryList = binary.split()
    count = 0
    #Add leading zeros
    for x in binaryList:
        binaryList[count] = ("0" * (8 - len(binaryList[count]))) + binaryList[count]
        count += 1

    # Function to mirror the byte
    def bitMirror(byte):
        return byte[::-1]
    flipkey = ""
    # turn back into binary
    for x in binaryList:
        flipkey += struct.pack('B', int(bitMirror(x), 2))
    #Pad with NULL bytes
    flipkey += "\x00" * (8 - len(flipkey))
    #Encryptwith DES
    des = DES.new(flipkey, DES.MODE_ECB)

    #challenge from server
    challenge = chall
#    challenge= chall.decode("hex")
    response = des.encrypt(challenge)
#    return ''.join(x.encode('hex') for x in response)
    return response


class ProtoVnc:
    def __init__(self):
        self.password = "testtest"
        self.challenge = None

    def onPreSend(self, data, index):
        # encode challenge we received with the password
        if index == 5:
            # if did not receive a valid challenge... we just dont care
            # do nothing, let all else fail
            if self.challenge is not None and len(self.challenge) == 16:
                #print " Encrypt: " + hexdump.dump(self.challenge)
                data = handshake(self.password, self.challenge)
                #print " Result:  " + hexdump.dump(data)

        return data


    # here we will receive the challenge
    def onPostRecv(self, data, index):
        if index == 4:
            #print "    " + hexdump.dump(data)
            self.challenge = data

        return data
