#!/usr/bin/python

import time
import os
import logging

sleeptimes = {
    # wait time, so the asan file really appears
    # used on every crash, should be short
    "sleep_for_asan_file": 0.5,
}


# create an array of the binary path and its parameters
# used to start the process with popen() etc.
def getInvokeTargetArgs(config, targetPort):
    args = config["target_args"] % ( { "port": targetPort } )
    argsArr = args.split(" ")
    cmdArr = [ config["target_bin"] ]
    cmdArr.extend( argsArr )
    return cmdArr


def setupEnvironment(config):
    """
    Prepare the environment before the server is started
    (e.g. working directory)
    """
    # Silence warnings from the ptrace library
    #logging.getLogger().setLevel(logging.ERROR)

    # Most important is to set log_path so we have access to the asan logs
    asanOpts = ""
    asanOpts += "color=never:verbosity=0:leak_check_at_exit=false:"
    asanOpts += "abort_on_error=true:log_path=" + config["temp_dir"] + "/asan"
    os.environ["ASAN_OPTIONS"] = asanOpts

    # Tell Glibc to abort on heap corruption but not dump a bunch of output
    os.environ["MALLOC_CHECK_"] = "2"


def getAsanOutput(config, pid):
    global sleeptimes

    # as we cannot get stdout/stderr of child process, we store asan
    # output in the temp folder in the format: asan.<pid>
    fileName = config["temp_dir"] + "/asan." + str(pid)
    print "Get asan output: " + str(fileName)

    time.sleep(sleeptimes["sleep_for_asan_file"])  # omg wait for the file to appear

    if not os.path.isfile(fileName):
        logging.info("Did not find ASAN output file: " + fileName)
        #return "No ASAN file found (path: " + fileName + ")"
        return None
    else:
        logging.info("Found ASAN output file. Good.")

    # it may not exist, which aint bad (e.g. no asan support)
    file = open(fileName, "r")
    data = file.read()
    file.close()

    # remove the file, as we dont need it anymore
    os.remove(fileName)

    return data
