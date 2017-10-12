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
