#!/usr/bin/python

import sys
import glob
import os
import time
import pickle
import logging
import utils

import networkmanager

GLOBAL_SLEEP_REPLAY = {
    # how long to wait after server start
    # should be more like short because its used on every outcome
    "sleep_replay_after_server_start": 1,
}

def replayFindFile(config, index):
    outcomes = sorted(glob.glob(os.path.join(config["outcome_dir"], '*.raw')), key=os.path.getctime)
    return outcomes[int(index)]


def replayMessages(port, messages):
    networkManager = networkmanager.NetworkManager(None, port)
    networkManager.sendMessages(messages)


def replay(port, file):
    logging.basicConfig(level=logging.INFO)
    print "File: " + file
    print "Port: " + str(port)

    messages = None
    messages = utils.readPickleFile(file)
    replayMessages(port, messages)


def replayall(config, port):
    global GLOBAL_SLEEP_REPLAY
    print "Replay all files from directory: " + config["outcome_dir"]

    outcomeFiles = sorted(glob.glob(os.path.join(config["outcome_dir"], '*.pickle')), key=os.path.getctime)
    for outcomeFile in outcomeFiles:
        time.sleep( GLOBAL_SLEEP_REPLAY["sleep_replay_after_server_start"] ) # this is required, or replay is fucked. maybe use keyboard?
        replay(port, outcomeFile)


def main():
    if len(sys.argv) != 3:
        print "Usage: <picklefile> <serverpot>"
        return

    replay(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    main()
