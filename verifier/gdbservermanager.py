from subprocess import Popen, PIPE, STDOUT
import logging

import serverutils
import verifycrashdata
import re

from servermanager import ServerManager, StdoutQueue


class GdbServerManager(ServerManager):

    def __init__(self, config, queue_sync, queue_out, targetPort):
        ServerManager.__init__(self, config, queue_sync, queue_out, targetPort)
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

        crashData = verifycrashdata.VerifyCrashData()
        crashData.setData(
            backtrace=res,
            output=ret,
            cause="GDBSERVERMANAGER: n/a"
        )
        gdbOutput = serverutils.getAsanOutput(self.config, self.pid)
        if gdbOutput is not None:
            crashData.setAsan(gdbOutput)

        return crashData


    def _waitForCrash(self):
        logging.info("Wait for crash")

        # start gdb
        argsGdb = [ "/usr/bin/gdb", self.config["target_bin"], '-q' ]

        print "Start server: " + str(argsGdb)
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
