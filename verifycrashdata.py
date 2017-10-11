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
        self.registers = None
        self.stdOutput = None

        self.backtrace = None
        self.cause = None
        self.output = None

        self.temp = None


    def setData(self, faultAddress=None, faultOffset=None, module=None,
                sig=None, details=None, stackPointer=None, stackAddr=None,
                registers=None, cause=None, backtrace=None, output=None):
        self.faultAddress = faultAddress
        self.faultOffset = faultOffset
        self.module = module
        self.sig = sig
        self.details = details
        self.stackPointer = stackPointer
        self.stackAddr = stackAddr
        self.registers = registers

        self.backtrace = backtrace
        self.cause = cause
        self.output = output


    def setTemp(self, temp):
        self.temp = temp

    def getTemp(self):
        return self.temp

    def setStdOutput(self, stdout):
        self.stdOutput = stdout

    def printMe(self, who):
        print who + " Register : " + str(self.registers)
        print who + " Backtrace: " + str(self.backtrace)
        print who + " Cause    : " + str(self.cause)


    def getData(self):
        crashData = {
            "faultAddress": self.faultAddress,
            "faultOffset": self.faultOffset,
            "module": self.module,
            "sig": self.sig,
            "details": self.details,
            "stackPointer": self.stackPointer,
            "stackAddr": self.stackAddr,
            "registers": self.registers,
            "stdOutput": self.stdOutput,

            "backtrace": self.backtrace,
            "cause": self.cause,
            "output": self.output,
        }
        return crashData
