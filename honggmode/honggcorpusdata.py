#!/usr/bin/env python

from common.corpusdata import CorpusData


class HonggCorpusData(CorpusData):
    """
    Contains all information of input corpus (-files).

    A new CorpusFile may be created either by the process itself,
    or by another process, as indicated by isExternal.

    If it is external, it has to be processed: Sent to the target,
    but results ignored. This is indicasted by processed.
    """

    def __init__(self,
                 config,
                 filename,
                 networkData=None,
                 processed=True,
                 isExternal=False,
                 parentFilename=None):
        super(self.__class__, self).__init__(config, filename, networkData)

        self.processed = processed
        self.isExternal = isExternal

        self.stats['new'] = 0


    def isProcessed(self):
        return self.processed


    def statsAddNew(self):
        self.stats['new'] += 1


    def __str__(self):
        s = super(self.__class__, self).__str__()
        s += "Processed: " + str(self.processed) + "\n"
        s += "isExternal: " + str(self.isExternal) + "\n"
        return s
