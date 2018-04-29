#!/usr/bin/env python2

from netnslib import netns
import subprocess
import logging
import os


class LinuxNamespace(object):
    """
    Create a new network namespace.

    This allows multiple processes to bind to the same port.
    """

    def __init__(self, myid=0):
        self.namespaceName = 'ffw-' + str(myid)

        if os.geteuid() != 0:
            raise ValueError("Namespaces can only be used if you are root")

        nsPath = '/var/run/netns/' + self.namespaceName
        if not os.path.isfile(nsPath):
            subprocess.call( [ 'ip', 'netns', 'add', self.namespaceName ] )


    def apply(self):
        netns.NetNS(nsname=self.namespaceName)


    def startProcess(self, processArgs):
        with netns.NetNS(nsname=self.namespaceName):
            retcode = subprocess.call(processArgs)
            return retcode


    def cleanup(self):
        nsPath = '/var/run/netns/' + self.namespaceName
        if os.path.isfile(nsPath):
            subprocess.call( [ 'ip', 'netns', 'del', self.namespaceName ] )
