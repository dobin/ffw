#!/usr/bin/env python2

import os
import glob

import utils

sleeptimes = {
    # wait between server start and first connection attempt
    # so it can settle-in
    "wait_time_for_server_rdy": 0.1,

    # how long we let the server run
    # usually it should crash immediately
    "max_server_run_time": 1,
}


class Minimizer(object):
    """
    Minimize existing verified crash datas.

    This should provide an overrview of unique crashes, by parsing the
    .ffw pickle files with verify data, and aggregating them nicely.
    """

    def __init__(self, config):
        self.config = config


    def minimizeOutDir(self):
        outcomesDir = os.path.abspath(self.config["outcome_dir"])
        outcomesFiles = glob.glob(os.path.join(outcomesDir, '*.ffw'))
        crashes = dict()

        print(("Processing %d outcome files" % len(outcomesFiles)))

        for outcomeFile in outcomesFiles:
            crashDetails = self.readCrashDetails(outcomeFile)

            if crashDetails is not None and "faultOffset" in crashDetails:
                idx = crashDetails["faultOffset"]
                if idx not in crashes:
                    crashes[idx] = []

                crashes[idx].append(crashDetails)

        self.showMinimizeOverview(outcomesFiles, crashes, 69)


    def showMinimizeOverview(self, outcomesFiles, crashes, noCrash):

        print("Number of outcomes: " + str(len(outcomesFiles)))
        print("Number of no crashes: " + str(noCrash))

        # manage all these crashes
        for crash in crashes:
            print("Crashes in Offset: %s" % hex(crash))
            for details in crashes[crash]:
                print(("  Crash: %s" % details["file"]))
                print(("    Offset: %s" % hex(details["faultOffset"])))
                print(("    Module: %s" % details["module"]))
                print(("    Signature: %s" % details["sig"]))
                print(("    Details: %s" % details["details"]))


    def readCrashDetails(self, fileName):
        data = utils.readPickleFile(fileName)
        return data
