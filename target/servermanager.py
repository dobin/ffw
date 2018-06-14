#!/usr/bin/env python2

import time
import logging
import os
import subprocess
import sys
import resource

import targetutils


GLOBAL_SLEEP = {
    # how long to wait after server start
    # can be high as it is not happening so often
    "sleep_after_server_start": 0.5,
}


# https://stackoverflow.com/questions/1689505/python-ulimit-and-nice-for-subprocess-call-subprocess-popen
# Not needed, kept for later
def preexec_fn():
    resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))


class ServerManager(object):
    """
        Manages the server (the fuzzing target) process.
        This includes:
            - handling the process (start, stop)
            - getting some crash information
    """
    def __init__(self,
                 config,
                 threadId,
                 targetPort,
                 prependCmdline=None,
                 hideChildOutput=True):
        self.config = config
        self.process = None
        self.targetPort = targetPort
        self.isDisabled = False
        self.hideChildOutput = hideChildOutput

        targetutils.setupEnvironment(self.config)

        popenArg = targetutils.getInvokeTargetArgs(self.config, self.targetPort)
        if prependCmdline is None:
            self.popenArg = popenArg
        else:
            self.popenArg = []
            self.popenArg.extend(prependCmdline)
            self.popenArg.extend(popenArg)


    def start(self):
        """Start the server process."""
        if self.isDisabled:
            return

        if not os.path.isfile(self.config["target_bin"]):
            logging.error("Could not find target file: " +
                          str(self.config["target_bin"]))
            sys.exit(1)

        self._runTarget()

        if self.process is None:
            return False
        else:
            logging.info("Start server PID: " + str(self.process.pid))
            return True


    def stop(self):
        """Stop the server."""
        if self.isDisabled or self.process is None:
            return

        logging.info("Stop server PID: " + str(self.process.pid))
        try:
            self.process.terminate()
        except:
            logging.info("Could not terminate server - already crashed?")


    def restart(self):
        if self.isDisabled:
            return

        self.stop()
        time.sleep(GLOBAL_SLEEP["sleep_after_server_start"])
        self.start()
        time.sleep(GLOBAL_SLEEP["sleep_after_server_start"])


    def dis(self):
        self.isDisabled = True


    def _runTarget(self):
        """
        Actually start the server.
        """
        global GLOBAL_SLEEP
        logging.info("Starting server with args: " + str(self.popenArg))

        if self.hideChildOutput:
            # create devnull so we can us it to surpress output of the server
            # (2.7 specific)
            DEVNULL = open(os.devnull, 'wb')
            p = subprocess.Popen(
                self.popenArg,
                stdin=DEVNULL,
                stdout=DEVNULL,
                stderr=DEVNULL)
        else:
            # we want to see stdout / stderr
            p = subprocess.Popen(self.popenArg)

        # wait a bit so we are sure server is really started
        time.sleep( GLOBAL_SLEEP["sleep_after_server_start"] )
        logging.info("  Pid: " + str(p.pid) )

        # check if process is really alive (check exit code)
        returnCode = p.poll()
        logging.info("  Return code: " + str(returnCode))
        if returnCode is not None:
            # if return code is set (e.g. 1), the process exited
            return False

        self.process = p

        return True


    def getCrashInformation(self, crashData):
        """
        Return the data of the crash
        or None if it has not crashed (should not happen)
        """
        if self.isDisabled or self.process is None:
            msg = "Could not get crash information, process doesnt exist "
            msg += "(not started?): " + str(self.process)
            logging.warn(msg)
            return None

        try:
            if self.process.poll():
                logging.info("getCrashData(): get data, but server alive?!")
            else:
                logging.info("getCrashData(): ok, server is really crashed")
        except Exception as e:
            logging.warn("Could not poll process, strange: " + str(e))

        crashData.setCrashInformation(
            asanOutput=targetutils.getAsanOutput(self.config, self.process.pid),
            signum=0,
            exitcode=0,
            reallydead=self.process.poll(),
            serverpid=self.process.pid,
        )

        return crashData
