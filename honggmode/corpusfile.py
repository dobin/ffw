

class CorpusFile(object):
    """
    Contains all information of input corpus (-files).

    A new CorpusFile may be created either by the process itself,
    or by another process, as indicated by isExternal.

    If it is external, it has to be processed: Sent to the target,
    but results ignored. This is indicasted by processed.
    """

    def __init__(self, filename, data, processed=True, isExternal=False):
        self.data = data
        self.filename = filename
        self.processed = processed  #
        self.isExternal = isExternal
        self.stats = {
            'crashes': 0,
            'new': 0,
            'hangs': 0,
        }

        # backward compatibility
        n = 0
        for input in data:
            input["index"] = n
            n += 1


    def getData(self):
        return self.data


    def isProcessed(self):
        return self.processed


    def statsAddCrash(self):
        self.stats['crashes'] += 1


    def statsAddNew(self):
        self.stats['new'] += 1


    def statsAddHang(self):
        self.stats['hang'] += 1
