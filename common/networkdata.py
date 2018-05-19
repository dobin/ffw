#!/usr/bin/env python

import random
import logging

from utils import xstr


class NetworkData(object):
    def __init__(self, config, networkMessages):
        self.messages = networkMessages  # type: Array[]
        self.fuzzMsgIdx = None  # type: int
        self.fuzzMsgChoice = None  # type:

        if not self.messagesCheck():
            raise ValueError('NetworkMessages are invalid')

        # recover, if networkMessages is already fuzzed
        # Like when reading corpus file
        for idx, message in enumerate(self.messages):
            if 'isFuzzed' in message and message['isFuzzed']:
                self.fuzzMsxIdx = idx
                self.fuzzmsgChoice = message


    @staticmethod
    def createNetworkMessage(frm, data, index):
        msg = {
            "from": frm,
            "data": data,
            'index': index,
        }

        return msg


    def messagesCheck(self):
        return True


    def getRawData(self):
        return self.messages


    def selectMessage(self):
        while self.fuzzMsgIdx is None:
            random_index = random.randrange(0, len(self.messages))
            if self.messages[random_index]['from'] == 'cli':
                self.fuzzMsgIdx = random_index
                self.fuzzMsgChoice = self.messages[random_index]


    def setSelectedMessage(self, msgIdx):
        """
        Set which message was selected.
        An external fuzzer decided by its own which msg it wants
        to fuzz. selectMessage() was not called.
        """
        self.fuzzMsgIdx = msgIdx
        self.fuzzMsgChoice = self.messages[msgIdx]


    def getFuzzMessageData(self):
        return self.messages[self.fuzzMsgIdx]['data']


    def getFuzzMessageIndex(self):
        return self.fuzzMsgIdx


    def setFuzzMessageData(self, data):
        self.messages[self.fuzzMsgIdx]['data'] = data
        self.messages[self.fuzzMsgIdx]['isFuzzed'] = True


    def __str__(self):
        s = ""
        for msg in self.messages:
            if 'isFuzzed' in msg:
                d = ( msg['index'], len(msg['data']), True)
            else:
                d = ( msg['index'], len(msg['data']), False)
            s += "  Idx: %i  MsgLen: %i  isFuzzed: %r \n" % d

        s += "fuzzMsgIdx: " + str(self.fuzzMsgIdx)

        return s
