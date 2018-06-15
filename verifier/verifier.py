#!/usr/bin/env python2

import os
import multiprocessing
import Queue  # for Queue.Empty
import logging
import signal
import copy

from . import debugservermanager
from . import gdbservermanager
from network import networkmanager
from . import asanparser

from common.verifydata import VerifyData
from common.crashmanager import CrashManager


sleeptimes = {
    # wait between server start and first connection attempt
    # so it can settle-in
    "wait_time_for_server_rdy": 0.25,

    # how long we let the server run
    # usually it should crash immediately
    "max_server_run_time": 0.25,
}


class Verifier(object):
    """
    Verifies identified crashes.

    A successful verification is if:
    we replay the network messages, and the server crashes, which is
    indicated by either:
      - the process crashed
      - cannot connect anymore to the server
    """

    def __init__(self, config):
        self.config = config
        self.queue_sync = multiprocessing.Queue()  # connection to servermanager
        self.queue_out = multiprocessing.Queue()  # connection to servermanager
        self.serverPid = None  # pid of the server started by servermanager (not servermanager)
        self.p = None  # serverManager


    def verifyOutDir(self):
        """Verify all crashes."""
        crashManager = CrashManager(self.config)
        crashManager.loadCrashFiles()

        try:
            for crashData in crashManager:
                logging.info(("Now processing: " + crashData.filename))
                self._verifyCrash(crashData)

        except KeyboardInterrupt:
            # cleanup on ctrl-c
            try:
                self.p.terminate()
            except Exception as error:
                print("Exception: " + str(error))

            # wait for child to exit
            self.p.join()

    ########################

    def startChild(self, serverManager):
        p = multiprocessing.Process(target=serverManager.startAndWait, args=())
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

    ########################


    def _verifyCrash(self, crashData):
        serverCrashDataPtrace = self._verifyCrashWithPtrace(crashData)
        if serverCrashDataPtrace is None:
            # No crash? Just return, it will not be better
            return None
        if serverCrashDataPtrace.asanOutput is not None:
            serverCrashDataPtraceAsan = self._serverCrashDataWithPtraceAsan(
                serverCrashDataPtrace.asanOutput
            )
        else:
            serverCrashDataPtraceAsan = None
        serverCrashDataGdb = self._verifyCrashWithGdb(crashData)

        serverCrashDataMerged = self._mergeVerifyCrashData(
            serverCrashDataPtrace,
            serverCrashDataPtraceAsan,
            serverCrashDataGdb
        )

        if serverCrashDataPtrace is not None:
            verifyData = VerifyData(
                self.config,
                crashData,
                faultaddress=serverCrashDataPtrace.faultAddress,
                backtrace=serverCrashDataPtrace.backtrace,
                cause=serverCrashDataPtrace.cause,
                analyzerOutput=serverCrashDataPtrace.analyzerOutput,
                analyzerType=serverCrashDataPtrace.analyzerType
            )
            verifyData.writeToFile()

        if serverCrashDataGdb is not None:
            verifyData = VerifyData(
                self.config,
                crashData,
                faultaddress=serverCrashDataGdb.faultAddress,
                backtrace=serverCrashDataGdb.backtrace,
                cause=serverCrashDataGdb.cause,
                analyzerOutput=serverCrashDataGdb.analyzerOutput,
                analyzerType=serverCrashDataGdb.analyzerType
            )
            verifyData.writeToFile()

        if serverCrashDataPtraceAsan is not None:
            verifyData = VerifyData(
                self.config,
                crashData,
                faultaddress=serverCrashDataPtraceAsan.faultAddress,
                backtrace=serverCrashDataPtraceAsan.backtrace,
                cause=serverCrashDataPtraceAsan.cause,
                analyzerOutput=serverCrashDataPtraceAsan.analyzerOutput,
                analyzerType=serverCrashDataPtraceAsan.analyzerType
            )
            verifyData.writeToFile()

        if serverCrashDataMerged is not None:
            verifyData = VerifyData(
                self.config,
                crashData,
                faultaddress=serverCrashDataMerged.faultAddress,
                backtrace=serverCrashDataMerged.backtrace,
                cause=serverCrashDataMerged.cause,
                analyzerOutput=serverCrashDataMerged.analyzerOutput,
                analyzerType=serverCrashDataMerged.analyzerType
            )
            verifyData.writeToFile()


    def _verifyCrashWithPtrace(self, crashData):
        # get normal PTRACE / ASAN output
        debugServerManager = debugservermanager.DebugServerManager(
            self.config,
            self.queue_sync,
            self.queue_out,
            self.config["target_port"])
        debugVerifyCrashData = self._verify(crashData, debugServerManager)

        return debugVerifyCrashData


    def _serverCrashDataWithPtraceAsan(self, asanOutput):
        if not asanOutput:
            return None

        asanParser = asanparser.AsanParser()
        asanParser.loadData( asanOutput )
        asanVerifyCrashData = asanParser.getAsCrashData()

        return asanVerifyCrashData


    def _verifyCrashWithGdb(self, crashData):
        # get GDB output
        gdbServerManager = gdbservermanager.GdbServerManager(
            self.config,
            self.queue_sync,
            self.queue_out,
            self.config["target_port"])
        gdbVerifyCrashData = self._verify(crashData, gdbServerManager)
        return gdbVerifyCrashData


    def _mergeVerifyCrashData(self,
                              serverCrashDataPtrace,
                              serverCrashDataGdb,
                              serverCrashDataAsan):
        # Fix for broken debug
        # sometimes the process quits before python ptrace is able to get
        # it's data. Have to take the asan in that case
        if serverCrashDataPtrace.faultAddress == 0:
            logging.info("V: Base: asanVerifyCrashData")
            serverCrashData = copy.copy(serverCrashDataAsan)
        else:
            # Default: Lets use debugVerifyCrashData
            logging.info("V: Base: debugVerifyCrashData")
            serverCrashData = copy.copy(serverCrashDataPtrace)

        # add backtrace from Gdb
        if serverCrashDataGdb and serverCrashDataGdb.backtrace is not None:
            logging.info("V: BT: Use gdbVerifyCrashData")
            serverCrashData.backtrace = serverCrashDataGdb.backtrace
            serverCrashData.cause = serverCrashDataGdb.cause

        # add backtrace from ASAN if exists
        if serverCrashDataAsan and serverCrashDataAsan.backtrace is not None:
            logging.info("V: BT: Use asanVerifyCrashData")
            serverCrashData.backtrace = serverCrashDataAsan.backtrace
            serverCrashData.cause = serverCrashDataAsan.cause

        return serverCrashData


    def _verify(self, crashData, serverManager):
        # start the server in the background
        self.networkManager = networkmanager.NetworkManager(
            self.config,
            self.config["target_port"])
        self.startChild(serverManager)

        # wait for ok (pid) from child that the server has started
        data = self.queue_sync.get()
        serverPid = data[1]
        self.serverPid = serverPid
        logging.info("Verifier: Server pid: " + str(serverPid))

        res = self.networkManager.debugServerConnection()
        if not res:
            logging.error("Could not connect")
            return None

        logging.info("Verifier: Sending fuzzed messages")
        self.networkManager.sendMessages(crashData.corpusData.networkData)

        # get crash result data from child
        #   or empty if server did not crash
        # serverCrashData is type verifier:ServerCrashData
        try:
            logging.info("Verifier: Wait for crash data")
            (t, serverCrashData) = self.queue_sync.get(
                True,
                sleeptimes["max_server_run_time"])
            serverStdout = self.queue_out.get()

            # it may be that the debugServer detects a process exit
            # (e.g. port already used), and therefore sends an
            # empty result. has to be handled.
            if serverCrashData:
                logging.info("Verifier: I've got a crash")
                print("Verifier: crash verified: %s: %s " %
                      (crashData.filename, serverCrashData.faultAddress))
                serverCrashData.setProcessStdout(serverStdout)
            else:
                logging.error("Verifier: Some server error:")
                logging.error("Verifier: Output: " + serverStdout)

            return serverCrashData
        except Queue.Empty:
            logging.info("Verifier: no crash on: %s" % (crashData.filename) )
            print("Verifier: no crash on: %s" % (crashData.filename) )
            self.stopChild()
            return None

        return None
