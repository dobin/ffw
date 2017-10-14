
import logging
import serverutils


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


class ServerManager(object):
    """The actual debug-server manager."""

    def __init__(self, config, queue_sync, queue_out, targetPort):
        self.config = config
        self.queue_sync = queue_sync
        self.queue_out = queue_out
        self.targetPort = targetPort

        self.pid = None

        self.stdoutQueue = StdoutQueue(queue_out)
        serverutils.setupEnvironment(config)


    # entry function for this new process
    # should be the only public function
    def startAndWait(self):
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

        logging.info("Server PID: " + str(self.pid))

        # notify parent about the pid
        self.queue_sync.put( ("pid", self.pid) )

        if self._waitForCrash():
            crashData = self._getCrashDetails()
        else:
            crashData = None

        # _getCrashDetails could return None
        if crashData is not None:
            #logging.debug("DebugServer: send to queue_sync")
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
