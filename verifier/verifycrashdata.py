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

    def __init__(self, faultAddress=None, faultOffset=None, module=None,
                 sig=None, details=None, stackPointer=None, stackAddr=None,
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


    def getDataX(self):
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


    def __repr__(self):
        return "AAAAAAAAAAAAAAAAAAAAA"

    def __str__(self):
        return str(self.faultAddress) + self.backtrace + self.cause
