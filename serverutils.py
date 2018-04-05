#!/usr/bin/python

import time
import os
import logging
import defaultconfig
import sys
import resource

"""
Various target-server utilities.

Functions which makes it possible to start the server (fuzzing target),
and other similar stuff. Used by *servermanagers, which are abstractions
to the actual server, but use these functions here.
"""


def getInvokeTargetArgs(config, targetPort):
    """
    Create an array of the target binary path and its parameters.

    Used to start the process with popen() etc.
    """
    cmdArr = [ config["target_bin"] ]

    # only add arguments if there are really some (issue #23)
    if "target_args" in config and config["target_args"] is not "":
        args = config["target_args"] % ( { "port": targetPort } )
        argsArr = args.split(" ")
        cmdArr.extend( argsArr )

    return cmdArr


def setupEnvironment(config):
    """
    Prepare the environment before the server is started.

    For example asan options, working directory, ASLR and ulimit.
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

    # Check ASLR status
    if config["ignore_aslr_status"] is False:
        aslrStatusFile = "/proc/sys/kernel/randomize_va_space"
        d = ""
        with open(aslrStatusFile, "r") as f:
            d = f.read()
        config["env_aslr_status"] = d
        if "disable_aslr_check" not in config and d is not "0":
            logging.error("ASLR Enabled, please disable it:")
            logging.error(" echo 0 | sudo tee /proc/sys/kernel/randomize_va_space")
            sys.exit(1)

    # set resources
    # core file:
    resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

    # set working directory
    # TODO FIXME


def getAsanOutput(config, pid):
    """Get ASAN output file based on the pid and config."""
    # as we cannot get stdout/stderr of child process, we store asan
    # output in the temp folder in the format: asan.<pid>
    fileName = config["temp_dir"] + "/asan." + str(pid)
    logging.info("Get asan output: " + str(fileName))

    # omg wait for the file to appear (necessary?)
    time.sleep(defaultconfig.DefaultConfig["sleep_for_asan_file"])

    # it may not exist, which aint bad (e.g. no asan support)
    if not os.path.isfile(fileName):
        logging.info("Did not find ASAN output file: " + fileName)
        return None
    else:
        logging.info("Found ASAN output file. Good.")

    file = open(fileName, "r")
    data = file.read()
    file.close()

    # remove the file, as we dont need it anymore
    os.remove(fileName)

    return data
