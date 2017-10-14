#!/usr/bin/env python2

import glob
import os
import time
import logging
import utils

import networkmanager

"""
Replay verified outcomes.

Used to replay a .ffw file from the verified/ directory.
This is mainly used to reproduce a crash outcome by running the
target manually in gdb. The messages have to be resent, including
proto implementations.
"""


GLOBAL_SLEEP_REPLAY = {
    # how long to wait after server start
    # should be more like short because its used on every outcome
    "sleep_replay_after_server_start": 1,
}


class Replayer():
    def __init__(self, config):
        self.config = config


    def replayMessages(self, port, messages):
        networkManager = networkmanager.NetworkManager(self.config, port)
        networkManager.sendMessages(messages)


    def replayFile(self, port, file):
        #logging.basicConfig(level=logging.INFO)
        print "File: " + file
        print "Port: " + str(port)

        p = utils.readPickleFile(file)
        messages = p["fuzzIterData"]["fuzzedData"]
        self.replayMessages(port, messages)


    def replayAllFiles(self, config, port):
        global GLOBAL_SLEEP_REPLAY
        print "Replay all files from directory: " + config["outcome_dir"]

        outcomeFiles = sorted(glob.glob(os.path.join(config["outcome_dir"], '*.ffw')), key=os.path.getctime)
        for outcomeFile in outcomeFiles:
            time.sleep( GLOBAL_SLEEP_REPLAY["sleep_replay_after_server_start"] )  # this is required, or replay is fucked. maybe use keyboard?
            self.replayFile(port, outcomeFile)
