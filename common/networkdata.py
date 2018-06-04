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

            message['latency'] = None
            message['timeouts'] = 0


    @staticmethod
    def createNetworkMessage(frm, data, index):
        msg = {
            "from": frm,
            "data": data,
            'index': index,

            'latency': None,
            'timeouts': 0,
        }

        return msg


    def messagesCheck(self):
        return True


    def getRawData(self):
        return self.messages


    def selectMessage(self):
        """
        We decide which message we want to mutate.
        It will be fuzzed (changed) after this function.
        Mostly used for file-based mutators.
        """
        while self.fuzzMsgIdx is None:
            random_index = random.randrange(0, len(self.messages))
            if self.messages[random_index]['from'] == 'cli':
                self.fuzzMsgIdx = random_index
                self.fuzzMsgChoice = self.messages[random_index]


    def setSelectedMessage(self, msgIdx):
        """
        Set which message was selected.
        An external mutator decided by its own which msg it wants
        to mutate. selectMessage() was not called. The message
        is already mutated, we just need to specify it here.
        Mostly used by class-based mutators.
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


    def updateMessageLatency(self, idx, latency):
        if self.messages[idx]['latency'] is None:
            self.messages[idx]['latency'] = latency
        else:
            self.messages[idx]['latency'] = (self.messages[idx]['latency'] + latency) / 2


    def updateMessageTimeoutCount(self, idx):
        self.messages[idx]['timeouts'] += 1


    def getMaxLatency(self):
        max = 0
        for message in self.messages:
            if message['latency'] is not None:
                if message['latency'] > max:
                    max = message['latency']

        return max


    def __str__(self):
        s = ""
        for msg in self.messages:
            if 'isFuzzed' in msg:
                d = ( msg['index'], msg['from'], len(msg['data']), True, str(msg['latency']), str(msg['timeouts']))
            else:
                d = ( msg['index'], msg['from'], len(msg['data']), False, str(msg['latency']), str(msg['timeouts']))
            s += "  Idx: %2i  From: %s  MsgLen: %4i  isFuzzed: %r  latency: %s  timeouts: %s\n" % d

            #if 'latency' in msg and msg['latency'] is not None:
            #    print("LATENCY: " + str(msg['latency']))


        s += "fuzzMsgIdx: " + str(self.fuzzMsgIdx)

        return s
