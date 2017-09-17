# FFW - Fuzzing For Worms

Fuzzes network servers.

## Requirements

* A network server which does not fork and accepts a port on the command line
* Data to be sent to the server in `inputs`

## Config

```
 sysctl net.core.somaxconn=4096
 ulimit -c 999999
```

## Install deps

```
sudo pip install python-ptrace
```

### Fix ptrace

/usr/local/lib/python2.7/dist-packages/ptrace/debugger/memory_mapping.py
```
PROC_MAP_REGEX = re.compile(
    r'([0-9a-f]+)-([0-9a-f]+) '
    r'(.{4}) '
    r'([0-9a-f]+) '
    r'([0-9a-f]+):([0-9a-f]+) ' ##### fix this
    r'([0-9]+)'
    r'(?: +(.*))?'
)
```

## install radamsa

```
$ git clone https://github.com/aoh/radamsa.git
$ cd radamsa
$ make
```


## Modes

Modes:
* fuzz
* minimize
* replayall
* replay

### Fuzz

* Fuzzes the program.
* creates .raw files in `outcome_dir`

### Minimize

* Goes through all .raw outcome files in `outcome_dir`
* Sends it to the server (`target_bin`), and looks for a crash
* If a crash is detecte, creates a `.crashdata.txt` file for that outome
* After all files have been processed: shows unique crashes (based on IP and other things)


### replaying

Send results in outcome to a dedicated server (e.g. in gdb).
If pre-requests / initial data are sent in the fuzzing, it is not just possible to
blindly send the `.raw` file in `outcome_dir`, as that request has also to be sent.
This replay functionality exists to reproduce crashes in an easy way.

#### Replayall

* Sends all outcomes in `outcome_dir/*.raw` to a server
* User has to start server by themself (e.g. in gdb)
* Used to check all outcomes

#### Replay

* Send a specific outcome in `outcome_dir` to the server
* either:
  * by its FULL path (.raw file)
  * or by its index (based on create time, as seen by replayall)
* User has to start server by themself (e.g. in gdb)

## Example config

```python
def sendInitialData(socket):
    authData = "\x10\x16\x00\x04\x4d\x51\x54\x54\x04\x02\x00\x00\x00\x0a\x6d\x79\x63\x6c\x69\x65\x6e\x74\x69\x64"
    socket.sendall(authData)


config = {
    "basedir": BASEDIR,
    "projdir": PROJDIR,

    # fuzzed files are generated here
    "temp_dir": PROJDIR + "temp",

    # where are input which crash stuff stored
    "outcome_dir" : PROJDIR + "out",

    # which fuzzer should be used
    "fuzzer": "Radamsa",

    # Path to target
    "target_bin" : PROJDIR + "bin/mqtt_broker",
    "target_args": "%(port)i", # not yet used TODO

    # Directory of input files
    "inputs_raw": PROJDIR + "in_raw", # TODO not yet used
    "inputs" : PROJDIR + "in",

    # if you have multiple ffw fuzzers active,
    # change this between them
    "baseport": 30000,

    # analyze response for information leak? (slow)
    "response_analysis": False,

    # TODO
    # check code coverage?
    "gcov_coverage": False,
    "gcov_coverage_time": 10000, # in iterations

    # crash analysis?
    "crash_minimize": False,
    "crash_minimize_time": 3, # number of new crashes

    # TODO
    # Note: can also be manually started
    "corpus_destillation": False,

    # TODO
    # e.g. boofuzz
    "additional_fuzzer": False,

    # send data before the actual fuzzing packet
    # e.g. authentication
    "sendInitialDataFunction": sendInitialData,

    # how many fuzzing instances should we start
    # Note: server needs to support port on command line
    # for this feature to work
    "processes": 2,
}

```

## Compile targets

Use:
```
CFLAGS="-fsanitize=address -fno-omit-frame-pointer"
```

# FAQ

## Can i fuzz windows binaries?

No

## Can i fuzz closed source binaries?

Yes

# Fix
