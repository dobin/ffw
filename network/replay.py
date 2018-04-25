#!/usr/bin/env python2

import logging

from . import networkmanager
from common.ffwfile import FfwFile


class Replayer(object):
    def __init__(self, config):
        self.config = config


    def replayFile(self, port, file):
        ffwFile = FfwFile(self.config)

        if ffwFile is None:
            print "ERror"

        networkData = ffwFile.getNetworkData(file)

        networkManager = networkmanager.NetworkManager(self.config, port)
        networkManager.sendMessages(networkData)
