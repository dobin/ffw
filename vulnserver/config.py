# this is a dedicated configuration file
# the same content as fuzzing.py

{
    # name of the software we fuzz
    "name": "vulnserver",

    # which version of the software are we fuzzing (optional)
    "version": "",

    # additional comment about this project (optional)
    "comment": "",

    # Path to target
    "target_bin": "bin/vulnserver_plain_asan",

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

    "honggpath": "/Development/honggfuzz/honggfuzz",

    "use_netnamespace": False,
}
