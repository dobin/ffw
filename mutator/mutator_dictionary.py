import copy
import logging
import os


class MutatorDictionary(object):

    def __init__(self, threadId, seed, dictDir, threadCount=1):
        self.seed = seed
        self.entry = {
            'networkMsg': 0,
            'byteOffset': 0,
            'word': None,
            'replaceWordIdx': 0,
            'counter': 0,
        }

        self.dict = [ ]
        self.threadId = threadId
        self.threadCount = threadCount
        self.index = {}  # corpusData -> []entry

        dictpath = os.path.join(dictDir, 'dictionary.txt')
        self._loadDict(dictpath)


    def _loadDict(self, dictpath):
        with open(dictpath, 'r') as f:
            self.dict = f.readlines()

        self.dict = [x.strip() for x in self.dict]


    def _createIndex(self, corpusData):
        corpusIndex = []
        tempIndex = []
        for word in self.dict:
            for msgIdx, msg in enumerate(corpusData.networkData.messages):
                # only fuzz client messages
                if msg['from'] != 'cli':
                    continue

                pos = -1
                # find (multiple) of word in msg
                while True:
                    try:
                        pos = msg['data'].index(word, pos + 1)
                        entry = {
                            'networkMsg': msgIdx,
                            'byteOffset': pos,
                            'word': word,
                            'replaceWordIdx': 0,
                            'counter': 0,
                        }
                        tempIndex.append(entry)
                    except Exception as e:
                        break

        n = self.threadId
        while n < len(tempIndex):
            corpusIndex.append( tempIndex[n] )
            n += self.threadCount

        return corpusIndex


    def fuzz(self, corpusData):
        # check if data already exists
        corpusIndex = None
        if corpusData in self.index:
            corpusIndex = self.index[corpusData]
        else:
            corpusIndex = self._createIndex(corpusData)
            self.index[corpusData] = corpusIndex

        # find first unhandled one
        for entry in corpusIndex:
            # entry is not finished processing?
            if entry['replaceWordIdx'] < len(self.dict) - 1:
                fuzzedCorpus = self._getFuzzedCorpus(corpusData, entry)
                entry['replaceWordIdx'] += 1
                return fuzzedCorpus


    def _getReplaceWord(self, word, wordIndex):
        replaceWord = self.dict[wordIndex]
        if replaceWord == word:
            newIdx = wordIndex + 1
            if newIdx > len(self.dict):
                newIdx = 0
            replaceWord = self.dict[newIdx]

        return replaceWord


    def _getFuzzedCorpus(self, corpusData, entry):
        fuzzedCorpus = corpusData.createFuzzChild(str(entry['counter']))

        data = fuzzedCorpus.networkData.messages[ entry['networkMsg'] ]['data']
        replaceWord = self._getReplaceWord(entry['word'], entry['replaceWordIdx'])

        # replace all occurences (not what we want)
        # data = data.replace(entry['word'], replaceWord)

        # replace one occurence
        # s = s[:position] + replacement + s[position+length_of_replaced:]
        data = data[:entry['byteOffset']] + replaceWord + data[entry['byteOffset'] + len(entry['word']):]

        fuzzedCorpus.networkData.messages[ entry['networkMsg'] ]['data'] = data
        fuzzedCorpus.networkData.setSelectedMessage(entry['networkMsg'])
        entry['counter'] += 1

        return fuzzedCorpus
