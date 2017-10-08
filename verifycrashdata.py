#!/usr/bin/env python2

import asanparser

"""
Data Model used on verify crashes.

Contains all data from a successfuly reproduced crash;
- address sanitizer output
- backtrace
- instruction pointer
- and more

Used by:
- DebugServerManager
- Verifier
"""


class VerifyCrashData():

    def __init__(self):
        self.faultAddress = None
        self.faultOffset = None
        self.module = None
        self.sig = None
        self.details = None
        self.stackPointer = None
        self.stackAddr = None
        self.backtrace = None
        self.registers = None
        self.asanOutput = None
        self.asanData = None
        self.stdOutput = None


    def setData(self, faultAddress=None, faultOffset=None, module=None,
                sig=None, details=None, stackPointer=None, stackAddr=None,
                backtrace=None, registers=None):
        self.faultAddress = faultAddress
        self.faultOffset = faultOffset
        self.module = module
        self.sig = sig
        self.details = details
        self.stackPointer = stackPointer
        self.stackAddr = stackAddr
        self.backtrace = backtrace
        self.registers = registers

    def p(self):
        print "A: " + self.asanOutput
        print "B: " + str(self.asanData)
        return ""

    def setAsan(self, asanOutput):
        print "XXX: " + str(asanOutput)
        asanParser = asanparser.AsanParser()
        asanParser.loadData(asanOutput)

        self.asanOutput = asanOutput
        self.asanData = asanParser.getAsanData()

    def getAsanOutput(self):
        return self.asanOutput


    def setStdOutput(self, stdout):
        self.stdOutput = stdout


    def getData(self):
        if not self.asanData:
            self.asanData = ""
        if not self.asanOutput:
            self.asanOutput = ""

        crashData = {
            "faultAddress": self.faultAddress,
            "faultOffset": self.faultOffset,
            "module": self.module,
            "sig": self.sig,
            "details": self.details,
            "stackPointer": self.stackPointer,
            "stackAddr": self.stackAddr,
            "backtrace": self.backtrace,
            "registers": self.registers,
            "asanOutput": self.asanOutput,
            "asanData": self.asanData,
            "stdOutput": self.stdOutput,
        }
        return crashData
