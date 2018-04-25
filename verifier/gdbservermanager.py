#!/usr/bin/env python

from subprocess import Popen, PIPE, STDOUT
import logging
import re

from servercrashdata import ServerCrashData
from target import targetutils
from abstractverifierservermanager import AbstractVerifierServerManager


class GdbServerManager(AbstractVerifierServerManager):

    def __init__(self, config, queue_sync, queue_out, targetPort):
        AbstractVerifierServerManager.__init__(self, config, queue_sync, queue_out, targetPort)
        self.gdbOutput = None


    def _getCrashDetails(self):
        ret = self.gdbOutput
        logging.info("get crash details, res: " + str(len(ret)))
        p = re.compile('#.*\(gdb\)', re.S)
        backtrace = re.search(p, ret, flags=0).group()
        #self.queue_stdout.put(backtrace)
        backtraceFrames = backtrace.split('\n')
        i = 0
        res = []
        while(i < len(backtraceFrames)):
            if backtraceFrames[i].startswith("#"):
                res.append(backtraceFrames[i].rstrip("\n\r"))
            i += 1

        serverCrashData = ServerCrashData(
            backtrace=res,
            analyzerOutput=ret,
            analyzerType="gdb"
        )
        gdbOutput = targetutils.getAsanOutput(self.config, self.pid)
        if gdbOutput is not None:
            serverCrashData.setAsan(gdbOutput)

        return serverCrashData


    def _waitForCrash(self):
        logging.info("Wait for crash")

        # start gdb
        argsGdb = [ "/usr/bin/gdb", self.config["target_bin"], '-q' ]

        print("Start server: " + str(argsGdb))
        p = Popen(argsGdb, stdout=PIPE, stdin=PIPE, stderr=PIPE)

        data1 = "r " + self.config["target_args"] % ( { "port": self.targetPort } )
        data1 += "\nbt\n"
        ret = p.communicate(input=data1)[0]
        self.gdbOutput = ret

        return True


    def _startServer(self):
        pass

    def _stopServer(self):
        pass
