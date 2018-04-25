import logging


class ServerCrashData():

    def __init__(self,
                 faultAddress=None,
                 faultOffset=0,
                 module=None,
                 sig=0,
                 details=None,
                 stackPointer=None,
                 stackAddr=None,
                 registers=None,
                 processStdout=None,
                 cause=None,
                 backtrace=None,
                 analyzerOutput=None,
                 analyzerType=None,
                 asanOutput=None):

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
        self.asanOutput = asanOutput

        self.stdout = None


    def setProcessStdout(self, stdout):
        self.processStdout = stdout
