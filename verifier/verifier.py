#!/usr/bin/env python2

import time
import os
import glob
import multiprocessing
import Queue
import logging
import signal
import pickle
import copy

import debugservermanager
import gdbservermanager
import networkmanager
import utils
import asanparser
import verifierresult

"""
Crash Verifier

Verify crashes stored in:
  ./out

And put successfully verified into:
  ./verified

A successful verification is if:
we replay the network messages, and the server crashes, which is
indicated by either:
  - the process crashed
  - cannot connect anymore to the server
"""


sleeptimes = {
    # wait between server start and first connection attempt
    # so it can settle-in
    "wait_time_for_server_rdy": 0.5,

    # how long we let the server run
    # usually it should crash immediately
    "max_server_run_time": 2,
}


class Verifier(object):

    def __init__(self, config):
        self.config = config
        self.queue_sync = multiprocessing.Queue()  # connection to servermanager
        self.queue_out = multiprocessing.Queue()  # connection to servermanager
        self.serverPid = None  # pid of the server started by servermanager (not servermanager)
        self.p = None  # serverManager


    def startChild(self, debugServerManager):
        p = multiprocessing.Process(target=debugServerManager.startAndWait, args=())
        p.start()
        self.p = p


    def stopChild(self):
        logging.debug("Terminate child...")
        if self.p is not None:
            self.p.terminate()

        logging.debug("Kill server: " + str(self.serverPid))

        if self.serverPid is not None:
            try:
                os.kill(self.serverPid, signal.SIGTERM)
                os.kill(self.serverPid, signal.SIGKILL)
            except Exception as e:
                logging.error("Kill exception, but child should be alive: " + str(e))

        self.p = None
        self.serverPid = None


    def verifyFile(self, filename):
        """Verify a single file."""
        targetPort = self.config["baseport"] + 100
        self._verifyOutcome(targetPort, filename)


    def verifyOutDir(self):
        """Verify all files from the out directory."""
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
                self._verifyOutcome(targetPort, outcomeFile)
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


    def _verifyOutcome(self, targetPort, outcomeFile):
        outcome = utils.readPickleFile(outcomeFile)

        crashData = None
        crashDataDebug = None
        crashDataGdb = None
        crashDataAsan = None

        # get normal PTRACE / ASAN output
        debugServerManager = debugservermanager.DebugServerManager(self.config, self.queue_sync, self.queue_out, targetPort)
        crashDataDebug = self._verify(outcome, targetPort, debugServerManager)
        crashDataDebug.printMe("CrashDataDebug")

        # get ASAN (if available), and CORE (if available)
        # WORKAROUND, TODO
        asanOutput = crashDataDebug.getTemp()
        if asanOutput:
            asanParser = asanparser.AsanParser()
            asanParser.loadData( asanOutput )
            crashDataAsan = asanParser.getAsCrashData()
            crashDataAsan.printMe("CrashDataAsan")

        # get GDB output
        gdbServerManager = gdbservermanager.GdbServerManager(self.config, self.queue_sync, self.queue_out, targetPort)
        crashDataGdb = self._verify(outcome, targetPort, gdbServerManager)
        if crashDataGdb is not None:
            crashDataGdb.printMe("CrashDataGdb")

        # Default: Lets use crashDataDebug
        logging.info("V: Use crashDataDebug")
        crashData = copy.copy(crashDataDebug)

        # add backtrace from Gdb
        if crashDataGdb and crashDataGdb.backtrace is not None:
            logging.info("V: BT: Use crashDataGdb")
            crashData.backtrace = crashDataGdb.backtrace
            crashData.cause = crashDataGdb.cause

        # add backtrace from ASAN if exists
        if crashDataAsan and crashDataAsan.backtrace is not None:
            logging.info("V: BT: Use crashDataAsan")
            crashData.backtrace = crashDataAsan.backtrace
            crashData.cause = crashDataAsan.cause

        verifierResult = verifierresult.VerifierResult(
            crashDataDebug,
            crashDataAsan,
            crashDataGdb,
            crashData
        )

        outcome["verifierResult"] = verifierResult

        self._handleCrash(outcome)


    def _verify(self, outcome, targetPort, debugServerManager):
        # start server in background
        # TODO move this to verifyOutDir (more efficient?)

        #self.debugServerManager = debugservermanager.DebugServerManager(self.config, self.queue_sync, self.queue_out, targetPort)
        self.networkManager = networkmanager.NetworkManager(self.config, targetPort)
        self.startChild(debugServerManager)

        # wait for ok (pid) from child that the server has started
        data = self.queue_sync.get()
        serverPid = data[1]
        self.serverPid = serverPid
        logging.info("Verifier: Server pid: " + str(serverPid))
        self.networkManager.waitForServerReadyness()

        logging.info("Verifier: Sending fuzzed messages")
        self.networkManager.sendMessages(outcome["fuzzIterData"]["fuzzedData"])

        # get crash result data from child
        #   or empty if server did not crash
        try:
            logging.info("Verifier: Wait for crash data")
            (t, crashData) = self.queue_sync.get(True, sleeptimes["max_server_run_time"])
            serverStdout = self.queue_out.get()

            # it may be that the debugServer detects a process exit
            # (e.g. port already used), and therefore sends an
            # empty result. has to be handled.
            if crashData:
                logging.info("Verifier: I've got a crash: ")
                crashData.setProcessStdout(serverStdout)
            else:
                logging.error("Verifier: Some server error:")
                logging.error("Verifier: Output: " + serverStdout)

            return crashData
        except Queue.Empty:
            self._handleNoCrash()
            self.stopChild()
            return None

        return None


    def _handleCrash(self, outcome):
        logging.info("Handle a crash")
        self._savePickle(outcome)
        self._saveTxt(outcome)


    def _savePickle(self, outcome):
        # write pickle file
        fileName = os.path.join(self.config["verified_dir"],
                                str(outcome["fuzzIterData"]["seed"]) + ".ffw")
        with open(fileName, "w") as f:
            pickle.dump(outcome, f)


    def _saveTxt(self, outcome):
        verifierResult = outcome["verifierResult"]
        crashData = verifierResult.verifyCrashData
        gdbVerifyCrashData = verifierResult.gdbVerifyCrashData
        asanVerifyCrashData = verifierResult.asanVerifyCrashData


        # write text file
        fileName = os.path.join(self.config["verified_dir"],
                                str(outcome["fuzzIterData"]["seed"]) + ".txt")

        # handle registers
        if crashData.registers is not None:
            registerStr = ''.join('{}={} '.format(key, val) for key, val in crashData.registers.items())
        else:
            registerStr = ""

        # handle backtrace
        if crashData.backtrace is not None:
            backtraceStr = '\n'.join(map(str, crashData.backtrace))
        else:
            backtraceStr = ""

        asanOutput = ""
        gdbOutput = ""
        if asanVerifyCrashData is not None:
            asanOutput = asanVerifyCrashData.analyzerOutput
        if gdbVerifyCrashData is not None:
            gdbOutput = gdbVerifyCrashData.analyzerOutput

        with open(fileName, "w") as f:
            f.write("Address: %s\n" % hex(crashData.faultAddress))
            f.write("Offset: %s\n" % hex(crashData.faultOffset))
            f.write("Module: %s\n" % crashData.module)
            f.write("Signature: %s\n" % crashData.sig)
            f.write("Details: %s\n" % crashData.details)
            f.write("Stack Pointer: %s\n" % hex(crashData.stackPointer))
            f.write("Stack Addr: %s\n" % crashData.stackAddr)
            f.write("Registers: %s\n" % registerStr)
            f.write("Time: %s\n" % time.strftime("%c"))

            f.write("\n")
            f.write("Child Output:\n %s\n" % crashData.processStdout)
            f.write("Backtrace: %s\n" % backtraceStr)
            f.write("\n")
            f.write("ASAN Output:\n %s\n" % asanOutput)
            f.write("\n")
            f.write("GDB Output:\n %s\n" % gdbOutput)
            f.close()


    def _handleNoCrash(self):
        logging.info("Verifier: Waited long enough, NO crash. ")
