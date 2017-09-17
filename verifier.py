#!/usr/bin/env python2

import time
import os
import glob
import multiprocessing
import Queue
import logging
import shutil
import signal
import pickle

import debugservermanager
import networkmanager
import utils

sleeptimes = {
    # wait between server start and first connection attempt
    # so it can settle-in
    "wait_time_for_server_rdy": 0.1,

    # how long we let the server run
    # usually it should crash immediately
    "max_server_run_time": 1,
}


class Verifier(object):

    def __init__(self, config):
        self.config = config
        self.queue_sync = multiprocessing.Queue()  # connection to servermanager
        self.queue_out = multiprocessing.Queue()  # connection to servermanager
        self.serverPid = None  # pid of the server started by servermanager (not servermanager)
        self.p = None  # serverManager


    def handleCrash(self, outcome, crashData):
        print "Handlecrash"

        outcome["verifyCrashData"] = crashData
        # write pickle file
        fileName = os.path.join(self.config["verified_dir"],
                                str(outcome["fuzzIterData"]["seed"]) + ".ffw")
        with open(fileName, "w") as f:
            pickle.dump(outcome, f)

        # write text file
        fileName = os.path.join(self.config["verified_dir"],
                                str(outcome["fuzzIterData"]["seed"]) + ".txt")
        registerStr = ''.join('{}={} '.format(key, val) for key, val in crashData["registers"].items())
        backtraceStr = '\n'.join(map(str, crashData["backtrace"]))

        with open(fileName, "w") as f:
            f.write("Address: %s\n" % hex(crashData["faultAddress"]))
            f.write("Offset: %s\n" % hex(crashData["faultOffset"]))
            f.write("Module: %s\n" % crashData["module"])
            f.write("Signature: %s\n" % crashData["sig"])
            f.write("Details: %s\n" % crashData["details"])
            f.write("Stack Pointer: %s\n" % hex(crashData["stackPointer"]))
            f.write("Stack Addr: %s\n" % crashData["stackAddr"])
            f.write("Time: %s\n" % time.strftime("%c"))
            f.write("Child Output:\n %s\n" % crashData["stdOutput"])
            f.write("Registers: %s\n" % registerStr)
            f.write("Backtrace: %s\n" % backtraceStr)
            f.write("\n")
            f.write("ASAN Output:\n %s\n" % crashData["asanOutput"])
            f.close()


    def handleNoCrash(self):
        logging.info("Minimizer: Waited long enough, NO crash. ")
        self.stopChild()


    def startChild(self):
        p = multiprocessing.Process(target=self.debugServerManager.startAndWait, args=())
        p.start()
        self.p = p


    def stopChild(self):
        if self.p is not None:
            self.p.terminate()

        logging.debug("Kill: " + str(self.serverPid))

        if self.serverPid is not None:
            os.kill(self.serverPid, signal.SIGTERM)
            os.kill(self.serverPid, signal.SIGKILL)

        self.p = None
        self.serverPid = None


    def verifyOutcome(self, targetPort, outcomeFile):
        outcome = utils.readPickleFile(outcomeFile)

        # start server in background
        self.debugServerManager = debugservermanager.DebugServerManager(self.config, self.queue_sync, self.queue_out, targetPort)
        self.networkManager = networkmanager.NetworkManager(self.config, targetPort)

        self.startChild()

        # wait for ok (pid) from child that the server has started
        data = self.queue_sync.get()
        serverPid = data[1]
        self.serverPid = serverPid
        logging.info("Minimizer: Server pid: " + str(serverPid))
        self.networkManager.waitForServerReadyness()

        if not self.networkManager.openConnection():
            logging.error("Minimizer: Could not connect to server")

        self.networkManager.sendMessages(outcome["fuzzIterData"]["fuzzedData"])
        self.networkManager.closeConnection()

        # get crash result data from child
        #   or empty if server did not crash
        try:
            logging.info("Minimizer: Wait for crash data")
            (t, crashData) = self.queue_sync.get(True, sleeptimes["max_server_run_time"])
            serverStdout = self.queue_out.get()

            # it may be that the debugServer detects a process exit
            # (e.g. port already used), and therefore sends an
            # empty result. has to be handled.
            if crashData is not None:
                logging.info("Minimizer: I've got a crash")
                crashData["stdOutput"] = serverStdout
                self.handleCrash(outcome, crashData)
            else:
                logging.error("Some server error:")
                logging.error("Output: " + serverStdout)

            return crashData
        except Queue.Empty:
            self.stopChild()
            self.handleNoCrash()
            return None

        return None


    def verifyOutDir(self):
        logging.info("Crash verifier")

        outcomesDir = os.path.abspath(self.config["outcome_dir"])
        outcomesFiles = glob.glob(os.path.join(outcomesDir, '*.ffw'))

        n = 0
        noCrash = 0

        print("Processing %d outcome files" % len(outcomesFiles))

        try:
            for outcomeFile in outcomesFiles:
                print("Now processing: " + str(n) + ": " + outcomeFile)
                targetPort = self.config["baseport"] + n + 100


                self.verifyOutcome(targetPort, outcomeFile)

                n += 1

        except KeyboardInterrupt:
            # cleanup on ctrl-c
            try:
                self.p.terminate()
            except Exception as error:
                print "Exception: " + str(error)

            # wait for child to exit
            self.p.join()

        print "Number of outcomes: " + str(len(outcomesFiles))
        print "Number of no crashes: " + str(noCrash)
