#!/bin/python

import asanparser


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
        self.asanOuput = None
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


    def setAsan(self, asanOutput):
        asanParser = asanparser.AsanParser()
        asanParser.loadData(asanOutput)

        self.asanOutput = asanOutput
        self.asanData = asanParser.getAsanData()


    def setStdOutput(self, stdout):
        self.stdOutput = stdout


    def getData(self):
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
