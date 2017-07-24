#!/usr/bin/python
#
# Process crashes to determine uniqueness
#
# Based on: 
#   Framework for fuzzing things
#   author: Chris Bisnett

import glob
import os
import sys

from ptrace.debugger.debugger import PtraceDebugger
from ptrace.debugger.child import createChild
from ptrace.debugger.process_event import ProcessExit
from ptrace.debugger.ptrace_signal import ProcessSignal
from signal import SIGCHLD

import framework

def getCrashDetails(event):
    # Get the address where the crash occurred
    faultAddress = event.process.getInstrPointer()

    # Find the module that contains this address
    # Now we need to turn the address into an offset. This way when the process
    # is loaded again if the module is loaded at another address, due to ASLR,
    # the offset will be the same and we can correctly detect those as the same
    # crash
    module = None
    faultOffset = 0
    for mapping in event.process.readMappings():
        if faultAddress >= mapping.start and faultAddress < mapping.end:
            module = mapping.pathname
            faultOffset = faultAddress - mapping.start
            break

    # Apparently the address didn't fall within a mapping
    if module is None:
        module = "Unknown"
        faultOffset = faultAddress

    # Get the signal
    signal = event.signum

    # Get the details of the crash
    details = event._analyze().text

    return faultOffset, module, signal, details

def bin_crashes(config):
    print "bin crashes"
    sys.exit(0)
    # Tell Glibc to abort on heap errors but not dump a bunch of output
    os.environ["MALLOC_CHECK_"] = "2"

    crashes = dict()

    outcomesDir = os.path.abspath(config["outcome_dir"])
    outcomes = glob.glob(os.path.join(outcomesDir, '*.raw'))

    print "Processing %d outcomes" % len(outcomes)

    for outcome in outcomes:
        # Run the target with the outcome file to capture the crash. This will
        # start the process and have it wait for a ptrace attach
#        pid = createChild(
#            [
#                "/home/vagrant/ffv/fuzzme/fuzzme",
#                os.path.join(outcomesDir, outcome)
#            ],
#            True,
#            None
#        )
        framework.startServer(config)
        pid = GLOBAL["process"].pid

        # Attach to the target with ptrace
        dbg = PtraceDebugger()
        proc = dbg.addProcess(pid, True)

        # Let the process run now that we're attached
        proc.cont()

        # Wait for the event
        event = None
        while True:
            event = dbg.waitProcessEvent()

            # If this is a process exit we need to check if it was abnormal
            if type(event) == ProcessExit:
                if event.signum is None or event.exitcode == 0:
                    # Clear the event since this was a normal exit
                    event = None

            # If this is a signal we need to check if we're ignoring it
            elif type(event) == ProcessSignal:
                if event.signum == SIGCHLD:
                    # Ignore these signals and continue waiting
                    continue

            break

        # Verify the crash reproduced
        if event is None:
            continue

        # Process the event to get the details
        faultOffset, module, signal, details = getCrashDetails(event)

        signature = (faultOffset, module, signal)
        if signature not in crashes:
            crashes[signature] = details

    for crash in crashes:
        offset, module, signal = crash
        print "Crash: %s+0x%x (signal %d)" % (module, offset, signal)
        print "\t%s" % crashes[crash]
