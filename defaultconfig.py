

DefaultConfig = {
    # which version of the software are we fuzzing (optional)
    "version": "",

    # additional comment about this project (optional)
    "comment": "",

    # should we use linux namespaces? (required root, therefore default off)
    "use_netnamespace": False,

    # how many fuzzing instances should we start
    "processes": 1,

    # should the fuzzer fork, or not?
    # Set to True for some debugging purposes
    "fuzzer_nofork": False,

    # hongg stuff
    "honggpath": "honggfuzz/honggfuzz",
    "honggcov": None,
    "honggmode_option": None,  # will be overwritten based on honggcov

    # should we abort if aslr is enabled?
    "ignore_aslr_status": True,

    # yet not 100% defined what it is doing, not necessary
    "handle_corefiles": False,

    # have a special app protocol implemented? use it here
    # this will load protocol.py in the projdir
    # the instance of protocol.py will be stored in protocolInstance
    "use_protocol": False,
    "protocolInstance": None,

    # the maximum network message number we will look at
    # (send, replay, test etc.)
    "maxmsg": None,

    # the maximum network message number we will fuzz
    "maxfuzzmsg": None,

    # analyze the response of the server?
    "response_analysis": False,

    # keep generated output files
    "keep_temp": False,

    # which fuzzer should be used
    "mutator": [ "Radamsa" ],

    # Dharma grammars
    "grammars": "grammars/",

    'tweetcrash': False,

    # input/output for fuzzer is generated here (so he can mutate it)
    # also ASAN log files
    "temp_dir": "temp",
    # fuzzing results are stored in out/
    "outcome_dir": "crashes",
    # Directory of input files
    "input_dir": "corpus",
    # Directory of verified files
    "verified_dir": "verified",

    # restart server every X fuzzing iterations
    "restart_server_every": 10000,

    # how long we wait for an server answer
    "recvTimeout": 0.03,  # 30/s

    # how long we wait to check if the server is up/down
    "connectTimeout": 0.2,

    # hides the target server stdout - or not (on certain phases)
    "hideTargetStdout": True,

    # Interpret hangs as crashes. Mostly experimental.
    "hangsAreCrashes": False,
}
