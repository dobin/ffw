#!/usr/bin/env python2


class ProtoVnc:

    def onPreSend(self, data, index):
        print "-> onpresend"
        return data


    def onPostRecv(self, data, index):
        print "-> Onpostrecv"
        return data
