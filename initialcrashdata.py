#!/bin/python


class InitialCrashData():

    def __init__(self):
        self.asanOuput = None
        self.signum = None
        self.exitcode = None
        self.reallydead = None
        self.serverpid = None
        self.fuzzerPos = None


    def setData(self, asanOutput=None, signum=None, exitcode=None, reallydead=None, serverpid=None):
        self.asanOutput = asanOutput
        self.signum = signum
        self.exitcode = exitcode
        self.reallydead = reallydead
        self.serverpid = serverpid

    def setFuzzerPos(self, fuzzerPos):
        self.fuzzerPos = fuzzerPos


    def getData(self):
        crashData = {
            "asanOutput": self.asanOutput,
            "signum": self.signum,
            "exitcode": self.exitcode,
            "reallydead": self.reallydead,
            "serverpid": self.serverpid,
            "fuzzerPos": self.fuzzerPos,
        }
        return crashData
