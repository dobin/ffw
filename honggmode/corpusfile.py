

class CorpusFile(object):

    def __init__(self, filename, data, processed=True):
        self.data = data
        self.filename = filename
        self.processed = processed

        # backward compatibility
        n = 0
        for input in data:
            input["index"] = n
            n += 1


    def getData(self):
        return self.data


    def isProcessed(self):
        return self.processed
