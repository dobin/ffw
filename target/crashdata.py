#!/bin/python

import pickle
import os


class CrashData():

    def __init__(self,
                 config,
                 corpusData,
                 fuzzerPos):
        self.config = config
        self.corpusData = corpusData
        self.fuzzerPos = fuzzerPos


    def setCrashInformation(self, asanOutput=None, signum=None, exitcode=None, reallydead=None, serverpid=None):
        self.asanOutput = asanOutput
        self.signum = signum
        self.exitcode = exitcode
        self.reallydead = reallydead
        self.serverpid = serverpid


    def getDataRaw(self):
        crashDataRaw = {
            "asanOutput": self.asanOutput,
            "signum": self.signum,
            "exitcode": self.exitcode,

            "reallydead": self.reallydead,
            "serverpid": self.serverpid,
            "fuzzerPos": self.fuzzerPos,
        }
        return crashDataRaw


    def writeToFile(self):
        seed = self.corpusData.seed

        data = {
            "crashData": self.getDataRaw(),
            "corpusData": self.corpusData.getRawData(),
        }

        # pickle file with everything
        with open(os.path.join(self.config["outcome_dir"], str(seed) + ".ffw"), "w") as f:
            pickle.dump(data, f)

        # Save a txt log
        with open(os.path.join(self.config["outcome_dir"], str(seed) + ".txt"), "w") as f:
            f.write("Seed: %s\n" % seed)
            f.write("Fuzzer: %s\n" % self.config["fuzzer"])
            f.write("Target: %s\n" % self.config["target_bin"])

            f.write("Fuzzerpos: %s\n" % self.fuzzerPos)
            f.write("Signal: %d\n" % self.signum)
            f.write("Exitcode: %d\n" % self.exitcode)
            f.write("Reallydead: %s\n" % str(self.reallydead))
            f.write("PID: %s\n" % str(self.serverpid))
            f.write("Asanoutput: %s\n" % self.asanOutput)
