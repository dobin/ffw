#!/bin/python

import time
import os
import glob
from multiprocessing import Process, Queue

import debugservermanager
import network
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
        self.queue_sync = Queue()
        self.queue_out = Queue()
        self.outcomesDir = os.path.abspath(self.config["outcome_dir"])
        self.outcomesFiles = glob.glob(os.path.join(self.outcomesDir, '*.pickle'))


    def handleCrashData(crashData):
        print "M: Crash!"

        crashData = crashData[1]
        crashOutput = queue_out.get()
        asanOutput = getAsanOutput(self.config, serverPid)
        details = crashData[3]
        signature = ( crashData[0], crashData[1], crashData[2] )
        details = {
            "faultOffset": crashData[0],
            "module": crashData[1],
            "signature": crashData[2],
            "gdbdetails": crashData[3],
            "output": crashOutput,
            "asan": asanOutput,
            "file": outcome,
        }
        storeValidCrash(self.config, signature, details)


    def handleNoCrash(self):
        print "M: Waited long enough, NO crash. "
        self.debugServerManager.stop()

        # timeout waiting for the data, which means the server did not crash
        # kill it, and receive the unecessary data
        # TODO: If os.kill throws an exception, it could not kill it, therefore
        #       the start of the server failed. Retry

        #try:
        #    notneeded1 = queue_sync.get(True, 1)
        #    crashOutput = queue_out.get(True, 1)
        #except:
        #    print "  M: !!!!!!!!!!! Exception: No data to get for non-crash :-("


    def minimizeOutcome(self, outcome, targetPort):
        # start server in background
        self.debugServerManager = debugservermanager.DebugServerManager(self.config, self.queue_sync, self.queue_out, targetPort)
        p = Process(target=self.debugServerManager.startAndWait, args=())
        p.start()

        # wait for ok (pid) from child that the server has started
        data = self.queue_sync.get()
        serverPid = data[1]
        print "M: Server pid: " + str(serverPid)
        time.sleep(sleeptimes["wait_time_for_server_rdy"]) # wait a bit till server is ready
        self.debugServerManager.waitForServerReadyness()

        if not self.debugServerManager.openConnection():
            logging.error("Could not connect to server")

        self.debugServerManager.sendMessages(outcome)
        self.debugServerManager.closeConnection()

        # get crash result data
        # or empty if server did not crash
        try:
            print "M: Wait for crash data"
            crashData = self.queue_sync.get(True, sleeptimes["max_server_run_time"])
            self.handleCrash(crashData)
            return signature, details
        except Exception as error:
            print "exception: " + str(error)
            self.handleNoCrash()
            return None, None


    def handleCrash(self, crashData):
        print "---------- Handle Crash: " + str(crashData)
        print "RIP: " + str(hex(crashData[0]))

    def minimizeOutDir(self):
        print "Crash minimize"

        crashes = dict()
        n = 0
        noCrash = 0

        print "Processing %d outcome files" % len(self.outcomesFiles)

        try:
            for outcomeFile in self.outcomesFiles:
                print "\nNow: " + str(n) + ": " + outcomeFile
                targetPort = self.config["baseport"] + n + 100

                outcome = utils.readPickleFile(outcomeFile)
                sig, details = self.minimizeOutcome(outcome, targetPort)

                if sig is not None:
                    crashes[sig] = details
                else:
                    noCrash += 1
                n += 1

        except KeyboardInterrupt:
            # cleanup on ctrl-c
            try:
                os.kill(serverPid, signal.SIGTERM)
            except:
                pass

            # wait for child to exit
            #p.join()

        print "Number of outcomes: " + str(len(self.outcomesFiles))
        print "Number of no crashes: " + str(noCrash)
        # manage all these crashes
        for crash in crashes:
            offset, mod, sig = crash
            details = crashes[crash]
            print "Crash: %s+0x%x (signal %d)" % (mod, offset, sig)
            print "\t%s" % details["gdbdetails"]
