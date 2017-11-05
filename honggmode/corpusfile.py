

class CorpusFile(object):


    def __init__(self, filename, data):
        self.data = data
        self.filename = filename

        # backward compatibility
        n = 0
        for input in data:
            input["index"] = n
            n += 1


    def getData(self):
        return self.data
