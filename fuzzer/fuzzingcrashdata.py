#!/bin/python


class FuzzingCrashData():

    def __init__(self, crashData):
        self.asanOutput = crashData["asanOutput"]
        self.signum = crashData["signum"]
        self.exitcode = crashData["exitcode"]
        self.reallydead = crashData["reallydead"]
        self.serverpid = crashData["serverpid"]


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
