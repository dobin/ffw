#!/usr/bin/python

import logging
import signal
import os
import time

from ptrace.debugger.debugger import PtraceDebugger
from ptrace.debugger.child import createChild
from ptrace.debugger.process_event import ProcessExit
from ptrace.debugger.ptrace_signal import ProcessSignal

from target import targetutils
from .abstractverifierservermanager import AbstractVerifierServerManager

from servercrashdata import ServerCrashData


class DebugServerManager(AbstractVerifierServerManager):
    def __init__(self, config, queue_sync, queue_out, targetPort):
        AbstractVerifierServerManager.__init__(self, config, queue_sync, queue_out, targetPort)
        self.dbg = None
        self.crashEvent = None
        self.proc = None
        self.p = None
        if config["debug"]:
            logging.basicConfig(level=logging.DEBUG)


    def _startServer(self):
        # create child via ptrace debugger
        # API: createChild(arguments[], no_stdout, env=None)
        logging.debug("DebugServerManager: starting " + str(targetutils.getInvokeTargetArgs(self.config, self.targetPort + 1000)))
        self.pid = createChild(
            targetutils.getInvokeTargetArgs(self.config, self.targetPort),
            True,  # no_stdout
            None,
        )

        # Attach to the process with ptrace and let it run
        self.dbg = PtraceDebugger()
        self.proc = self.dbg.addProcess(self.pid, True)
        self.proc.cont()

        time.sleep(1)

        # i dont think this works here...
        # FIXME
        event = self.dbg.waitProcessEvent(blocking=False)
        if event is not None and type(event) == ProcessExit:
            logging.error("DebugServerManager: Started server, but it already exited: " + str(event))
            return False

        return True


    def _stopServer(self):
        try:
            self.dbg.quit()
            os.kill(self.pid, signal.SIGTERM)
        except:
            # is already dead...
            pass


    def _waitForCrash(self):
        while True:
            logging.info("ServerManager: Debug: Waiting for process event")
            event = self.dbg.waitProcessEvent()
            logging.info("ServerManager: Debug: " + str(event))
            # If this is a process exit we need to check if it was abnormal
            if type(event) == ProcessExit:
                if event.signum is None or event.exitcode == 0:
                    # Clear the event since this was a normal exit
                    event = None

            # If this is a signal we need to check if we're ignoring it
            elif type(event) == ProcessSignal:
                if event.signum == signal.SIGCHLD:
                    # Ignore these signals and continue waiting
                    continue
                elif event.signum == signal.SIGTERM:
                    # server cannot be started, return
                    event = None
                    self.queue_sync.put( ("err", event.signum) )

            break

        if event is not None and event.signum != 15:
            logging.info("ServerManager: Debug: Event Result: Crash")
            self.crashEvent = event
            return True
        else:
            logging.info("ServerManager: Debug: Event Result: No crash")
            self.crashEvent = None
            return False


    def _getCrashDetails(self):
        event = self.crashEvent
        # Get the address where the crash occurred
        faultAddress = 0
        try:
            faultAddress = event.process.getInstrPointer()
        except Exception as e:
            # process already dead, hmm
            logging.info("DebugServerManager: GetCrashDetails exception: " + str(e))

        # Find the module that contains this address
        # Now we need to turn the address into an offset. This way when the process
        # is loaded again if the module is loaded at another address, due to ASLR,
        # the offset will be the same and we can correctly detect those as the same
        # crash
        module = None
        faultOffset = 0

        try:
            for mapping in event.process.readMappings():
                if faultAddress >= mapping.start and faultAddress < mapping.end:
                    module = mapping.pathname
                    faultOffset = faultAddress - mapping.start
                    break
        except Exception as error:
            logging.info("DebugServerManager: getCrashDetails Exception: " + str(error))
            # it always has a an exception...
            pass

        # Apparently the address didn't fall within a mapping
        if module is None:
            module = "Unknown"
            faultOffset = faultAddress

        # Get the signal
        sig = event.signum

        # Get the details of the crash
        details = None

        details = ""
        stackAddr = 0
        stackPtr = 0
        backtraceFrames = None
        pRegisters = None
        try:
            if event._analyze() is not None:
                details = event._analyze().text

            # more data
            stackAddr = self.proc.findStack()
            stackPtr = self.proc.getStackPointer()

            # convert backtrace
            backtrace = self.proc.getBacktrace()
            backtraceFrames = []
            for frame in backtrace.frames:
                backtraceFrames.append( str(frame) )

            # convert registers from ctype to python
            registers = self.proc.getregs()
            pRegisters = {}
            for field_name, field_type in registers._fields_:
                regName = str(field_name)
                regValue = str(getattr(registers, field_name))
                pRegisters[regName] = regValue

        except Exception as e:
            # process already dead, hmm
            logging.info(("DebugServerManager: GetCrashDetails exception: " + str(e)))


        asanOutput = targetutils.getAsanOutput(self.config, self.pid)

        serverCrashData = ServerCrashData(
            faultAddress=faultAddress,
            faultOffset=faultOffset,
            module=module,
            sig=sig,
            details=details,
            stackPointer=stackPtr,
            stackAddr=str(stackAddr),
            backtrace=backtraceFrames,
            registers=pRegisters,
            asanOutput=asanOutput,
            analyzerType='ptrace',
        )

        return serverCrashData
