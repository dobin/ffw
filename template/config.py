# this is a dedicated configuration file
# the same content as fuzzing.py

{
    # name of the software we fuzz
    "name": "",

    # which version of the software are we fuzzing (optional)
    "version": "",

    # additional comment about this project (optional)
    "comment": "",

    # Path to target
    "target_bin": "bin/server",

    # target arguments
    # separate arguments by space
    # keywords: ""%(port)i" is the port the server will be started on
    "target_args": "%(port)i",

    # if you cant specify the port on the command line,
    # hardcode it here. Note that it will work only with one fuzzing instance.
    "target_port": 20000,

    # how many fuzzing instances should we start
    "processes": 1,

    # "tcp" or "udp" protocol?
    "ipproto": "tcp",

    # STOP.
    # no need to change after this line, usually

    # hongg stuff
    "honggpath": "/opt/honggfuzz/honggfuzz",
    "honggcov": None,
    "honggmode_option": None,  # will be overwritten based on honggcov

    # should we abort if aslr is enabled?
    "ignore_aslr_status": True,

    # have a special app protocol implemented? use it here
    "proto": None,

    # the maximum network message number we will look at
    # (send, replay, test etc.)
    "maxmsg": None,

    # the maximum network message number we will fuzz
    "maxfuzzmsg": None,

    # analyze the response of the server?
    "response_analysis": True,

    # input/output for fuzzer is generated here (so he can mutate it)
    # also ASAN log files
    "temp_dir": "temp",

    # keep generated output files
    "keep_temp": False,

    # fuzzing results are stored in out/
    "outcome_dir": "out",

    # which fuzzer should be used
    # currently basically only radamsa
    "fuzzer": "Radamsa",

    #Dharma grammars
    "grammars": "grammars/",

    # Directory of input files
    "input_dir": "in",

    # Directory of verified files
    "verified_dir": "verified",

    # restart server every X fuzzing iterations
    "restart_server_every": 10000,
}
