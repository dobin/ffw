from . import corpusfile


class CorpusIterator(object):
    """The iter() of CorpusManager class."""

    def __init__(self, corpuses):
        self.corpuses = corpuses  # Type: Array[CorpusFile]
        self.current = 0  # Type: Int

    def __iter__(self):
        return self

    def next(self):
        if self.current >= len(self.corpuses):
            raise StopIteration
        else:
            self.current += 1
            return self.corpuses[self.current - 1]


class CorpusManager(object):
    """
    Manage the CorpusFiles
    """

    def __init__(self, config):
        self.corpus = []  # type: Array[CorpusFile]
        self.config = config  # type: Dict


    def __iter__(self):
        return CorpusIterator(self.corpus)


    def addNewCorpusFile(self, corpusFile):
        """This fuzzer found a new corpus."""
        corpusFile.write()
        self.corpus.append(corpusFile)


    def readNewCorpusFile(self, filename):
        """Another fuzzer found a new corpus."""
        corpusFile = CorpusFile(self.config, filename=filename)
        corpusFile.read()
        self.corpus.append(corpusFile)
