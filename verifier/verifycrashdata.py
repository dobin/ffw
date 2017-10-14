#!/usr/bin/env python2

import logging


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

    def __init__(self, faultAddress=None, faultOffset=0, module=None,
                 sig=0, details=None, stackPointer=None, stackAddr=None,
                 registers=None, processStdout=None,
                 cause=None, backtrace=None,
                 analyzerOutput=None, analyzerType=None):

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
        self.analyzerOutput = analyzerOutput
        self.analyzerType = analyzerType

        self.temp = None


    def setProcessStdout(self, stdout):
        self.processStdout = stdout

    def printMe(self, who):
        logging.debug(who + " Register : " + str(self.registers))
        logging.debug(who + " Backtrace: " + str(self.backtrace))
        logging.debug(who + " Cause    : " + str(self.cause))


    def setTemp(self, temp):
        self.temp = temp


    def getTemp(self):
        return self.temp

    def __repr__(self):
        d = ""
        d += "VerifyCrashData: " + "Faultaddress: " + str(self.faultAddress)

        if self.backtrace:
            d += " Has_Backtrace"
        else:
            d += " NO_Backtrace"

        if self.backtrace:
            d += " Has_Cause"
        else:
            d += " NO_Cause"

        if self.analyzerOutput:
            d += " Has_AnalyzerOutput"
        else:
            d += " NO_AnalyzerOutput"

        d += "\n"

        return d

    def __str__(self):
        d = ""
        d += "VerifyCrashData: " + "Faultaddress: " + str(self.faultAddress)

        if self.backtrace:
            d += " Has_Backtrace"
        else:
            d += " NO_Backtrace"

        if self.backtrace:
            d += " Has_Cause"
        else:
            d += " NO_Cause"

        if self.analyzerOutput:
            d += " Has_AnalyzerOutput"
        else:
            d += " NO_AnalyzerOutput"

        d += "\n"

        return d
