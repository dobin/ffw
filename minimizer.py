#!/bin/python

import time
import os
import glob
import multiprocessing
import Queue
import logging
import sys
import shutil 

import serverutils
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


class Minimizer(object):

    def __init__(self, config):
        self.config = config
        self.queue_sync = multiprocessing.Queue() # connection to servermanager
        self.queue_out = multiprocessing.Queue() # connection to servermanager
        self.serverPid = None # pid of the server started by servermanager (not servermanager)
        self.p = None # serverManager
        self.outcomesDir = os.path.abspath(self.config["outcome_dir"])
        self.outcomesFiles = glob.glob(os.path.join(self.outcomesDir, '*.pickle'))


    def handleCrash(self, crashData, pickleFile):
        print "Handlecrash"
        fileName = os.path.join(self.config["verified_dir"], crashData["file"] + ".crashdata.txt")
        print "fileName: " + fileName
        with open(fileName, "w") as f:
            f.write("Offset: %s\n" % crashData["faultOffset"])
            f.write("Module: %s\n" % crashData["module"])
            f.write("Signature: %s\n" % crashData["sig"])
            f.write("Details: %s\n" % crashData["details"])
            f.write("Time: %s\n" % time.strftime("%c"))
            f.write("Child Output:\n %s\n" % crashData["stdOutput"])
            f.write("\n")
            f.write("ASAN Output:\n %s\n" % crashData["asanOutput"])
            f.close()

        shutil.copy2(pickleFile, self.config["verified_dir"])
        shutil.copy2(fileName, self.config["verified_dir"])



    def storeValidCrash(self, config, signature, details):
        logging.info("Minimizer: Store crash")


    def handleNoCrash(self):
        logging.info("Minimizer: Waited long enough, NO crash. ")
        self.stopChild()


    def startChild(self):
        p = multiprocessing.Process(target=self.debugServerManager.startAndWait, args=())
        p.start()
        self.p = p


    def stopChild(self):
        try:
            self.p.terminate()
        except:
            pass
        self.p = None


    def minimizeOutcome(self, outcome, targetPort, outcomeFile):
        # start server in background
        self.debugServerManager = debugservermanager.DebugServerManager(self.config, self.queue_sync, self.queue_out, targetPort)
        self.networkManager = networkmanager.NetworkManager(self.config, targetPort)

        self.startChild()

        # wait for ok (pid) from child that the server has started
        data = self.queue_sync.get()
        serverPid = data[1]
        self.serverPid = serverPid
        logging.info("Minimizer: Server pid: " + str(serverPid))
        time.sleep(sleeptimes["wait_time_for_server_rdy"]) # wait a bit till server is ready
        self.networkManager.waitForServerReadyness()

        if not self.networkManager.openConnection():
            logging.error("Minimizer: Could not connect to server")

        self.networkManager.sendMessages(outcome)
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
                crashData["file"] = outcomeFile
                logging.info("Minimizer: I've got a crash")
                crashData["stdOutput"] = serverStdout
                self.handleCrash(crashData, outcomeFile)
            else:
                logging.error("Some server error:")
                logging.error("Output: " + serverStdout)

            return crashData
        except Queue.Empty:
            self.stopChild()
            self.handleNoCrash()
            return None

        return None


    def minimizeOutDir(self):
        logging.info("Crash minimize")

        crashes = dict()
        n = 0
        noCrash = 0

        print("Processing %d outcome files" % len(self.outcomesFiles))

        try:
            for outcomeFile in self.outcomesFiles:
                print("Now processing: " + str(n) + ": " + outcomeFile)
                targetPort = self.config["baseport"] + n + 100

                outcome = utils.readPickleFile(outcomeFile)
                crashDetails = self.minimizeOutcome(outcome, targetPort, outcomeFile)

                #if sig is not None:
                #    crashes[sig] = details
                #else:
                #    noCrash += 1
                n += 1

        except KeyboardInterrupt:
            # cleanup on ctrl-c
            try:
                self.p.terminate()
            except Exception as error:
                print "Exception: " + str(error)

            # wait for child to exit
            #p.join()

        print "Number of outcomes: " + str(len(self.outcomesFiles))
        print "Number of no crashes: " + str(noCrash)
        # manage all these crashes
        #for crash in crashes:
        #    offset, mod, sig = crash
        #    details = crashes[crash]
        #    print "Crash: %s+0x%x (signal %d)" % (mod, offset, sig)
        #    print "\t%s" % details["gdbdetails"]
