#!/usr/bin/env python2

import logging


class VerifierResult(object):
    def __init__(self,
                 debugVerifyCrashData,
                 asanVerifyCrashData,
                 gdbVerifyCrashData,
                 verifyCrashData):

        self.debugVerifyCrashData = debugVerifyCrashData
        self.asanVerifyCrashData = asanVerifyCrashData
        self.gdbVerifyCrashData = gdbVerifyCrashData
        self.verifyCrashData = verifyCrashData

    def __repr__(self):
        d = ""
        d += "VerifierResult: "
        d += str(self.debugVerifyCrashData)
        d += str(self.asanVerifyCrashData)
        d += str(self.gdbVerifyCrashData)
        d += str(self.verifyCrashData)
        return d
