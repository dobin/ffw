

class ClientManager(config, threadId, targetPort):
    print "Client Manager"

    def execute(self):
        print "Start client"


    def _runTarget(self):
        """
        Start the server
        """
        global GLOBAL_SLEEP
        popenArg = serverutils.getInvokeTargetArgs(self.config, self.targetPort)
        logging.info("Starting server with args: " + str(popenArg))

        os.chdir( self.config["projdir"] + "/bin")
        # create devnull so we can us it to surpress output of the server (2.7 specific)
        #DEVNULL = open(os.devnull, 'wb')
        #p = subprocess.Popen(popenArg, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)

        # we want to see stdout / stderr
        p = subprocess.Popen(popenArg)
        time.sleep( GLOBAL_SLEEP["sleep_after_server_start"] )  # wait a bit so we are sure server is really started
        logging.info("  Pid: " + str(p.pid) )

        # check if process is really alive (check exit code)
        returnCode = p.poll()
        logging.info("  Return code: " + str(returnCode))
        if returnCode is not None:
            # if return code is set (e.g. 1), the process exited
            return None

        return p
