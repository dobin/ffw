
import random

class NetworkData(object):
    def __init__(self, config, networkMessages):
        self.messages = networkMessages # type: Array[NetworkMessages]
        self.fuzzMsgIdx = None  # type: int


    def getRawData(self):
        return self.messages


    def selectMessage(self):
        while self.fuzzMsgIdx is None:
            random_index = random.randrange(0, len(self.messages))
            if self.messages[random_index]['from'] is 'cli':
                self.fuzzMsgIdx = random_index


    def getFuzzMessageData(self):
        return self.messages[self.fuzzMsgIdx]['data']


    def setFuzzMessageData(self, data):
        self.messages[self.fuzzMsgIdx]['data'] = data
        self.messages[self.fuzzMsgIdx]['isFuzzed'] = True
