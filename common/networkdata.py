import random

from utils import xstr


# Messages:
# [
#   {
#      'index': <int>,
#      'data': <string>
#      'from': <string> 'cli'/'srv'
#   }
# ]



class NetworkData(object):
    def __init__(self, config, networkMessages):
        self.messages = networkMessages  # type: Array[NetworkData]
        self.fuzzMsgIdx = None  # type: int
        self.fuzzMsgChoice = None  # type: NetworkData

        if not self.messagesCheck():
            raise ValueError('NetworkMessages are invalid')


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


    def getFuzzMessageData(self):
        return self.messages[self.fuzzMsgIdx]['data']


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
