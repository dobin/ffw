#!/usr/bin/env python

import logging
from target import targetutils


class StdoutQueue():
    """
    This is a Queue that behaves like stdout.

    Used to capture stdout events of the server/child.
    """

    def __init__(self, *args, **kwargs):
        self.q = args[0]

    def write(self, msg):
        self.q.put(msg)

    def flush(self):
        pass


class AbstractVerifierServerManager(object):
    """
    Abstract servermanager class.

    Actual servermanager for verifier/ will implement this abstract
    class for their purpose. E.g. a servermanager using either
    GDB or ptrace().
    Here we just implement the process-communication stuff with the
    parent process.
    """

    def __init__(self, config, queue_sync, queue_out, targetPort):
        self.config = config
        self.queue_sync = queue_sync
        self.queue_out = queue_out
        self.targetPort = targetPort

        self.pid = None

        self.stdoutQueue = StdoutQueue(queue_out)
        targetutils.setupEnvironment(config)


    def startAndWait(self):
        """
        Start target-server and wait for results.

        This is the only public function. All other communication
        is performed via queue_sync and queue_out, as this should be
        a separate process. No return value here.
        """
        # Sadly this does not apply to child processes started via
        # createChild(), so we can only capture output of this python process
        #sys.stdout = stdoutQueue
        #sys.stderr = stdoutQueue

        self.queue_out.put("Dummy")
        # do not remove print, parent excepts something
        logging.info("DebugServer: Start Server")
        #sys.stderr.write("Stderr")

        ret = self._startServer()
        while ret is False:
            logging.info("Retrying to start server...")
            ret = self._startServer()

        logging.info("DebugServer: Server PID: " + str(self.pid))

        # notify parent about the pid
        self.queue_sync.put( ("pid", self.pid) )

        # block until we have a crash
        # the client will send the network messages
        logging.info("DebugServer: Waiting for a crash")
        if self._waitForCrash():
            # seems we have a crash. get details, so we
            # can return it to the parent via queue_sync
            logging.info("DebugServer: We have a crash")
            crashData = self._getCrashDetails()
        else:
            logging.info("DebugServer: We have NO crash (timeout)")
            crashData = None

        # _getCrashDetails could return None
        if crashData is not None:
            logging.debug("DebugServer: send to queue_sync")
            self.queue_sync.put( ("data", crashData) )

        self._stopServer()


    def _stopServer(self):
        raise NotImplementedError()


    def _startServer(self):
        raise NotImplementedError()


    def _getCrashDetails(self, event):
        raise NotImplementedError()


    def _waitForCrash(self):
        raise NotImplementedError()
