# FFW - Fuzzing For Worms

Fuzzes network servers/services by intercepting valid network
communication data, then replay it with some fuzzing.

FFW can fuzz open source applications, and also closed
source applications. It also supports feedback driven fuzzing
by instrumenting honggfuzz, for both open- and closed source apps.

# Installation

## Install dependencies

```
pip install pyinotify
```

## Get ffw

```
git clone https://github.com/dobin/ffw.git
cd ffw/
```

## Install radamsa fuzzer

Default path specified in ffw for radamsa is `ffw/radamsa`:

```
$ git clone https://github.com/aoh/radamsa.git
$ cd radamsa
$ make
```

# Setup a project

Steps involved in setting up a fuzzing project:

* Create directory structure for that fuzzing project by copying template folder
* Copy target binary to bin/
* Specify all necessary information in the config file fuzzing.py
* Start interceptor-mode to record traffic
* Start test-mode to verify recorded traffic (optional)
* Start fuzz-mode to fuzz
* Start verify-mode to verify crashed from the fuzz mode (optional)
* Start upload-mode to upload verified crashes to the web (optional)

What follows are the detailed steps, by using the provided vulnserver as an example.


# Setup sample project

## Create directory structure

Create a copy of the template directory for the software you want to test, in this case vulnserver:

```
$ cd ffw/
$ cd vulnserver/
$ cp -R ../template/* .
```

The directory `vulnserver` will be our working directory from now on.
It will contain the file `fuzzing.py`, and the directories `in`, `bin`, `out`, `verified`, and `temp`.


## Compile the target

Copy the binary of the server you want to fuzz to bin. It is already prepared
in the `vulnserver/` directory, can be compiled with `make`:
```
$ make
gcc -O0 -fsanitize=address -fno-stack-protector -fno-omit-frame-pointer vulnserver.c -o vulnserver_asan
gcc -O0 -fno-stack-protector -fno-omit-frame-pointer vulnserver.c -o vulnserver_asan
$ cp ./vulnserver_asan ./bin
```

## Configure fuzzer

Edit `fuzzing.py` until STOP line. Specify the path to the binary, and how to give the port number
as parameter:
```
    "name": "vulnserver",
    "target_bin" : PROJDIR + "bin/vulnserver_asan",
    "target_args": "%(port)i",
    "ipproto": "tcp",
    "debug": True,
```

## Perform intercept

Start interceptor-mode. You can use the original standard port of the
server as argument. Port+1 will be used for the real server port:
```
$ ./fuzzing.py interceptor --port 1024
Debug mode enabled
INFO:root:Starting server with args: ['bin/vulnserver_asan', '1025']
INFO:root:  Pid: 21158
INFO:root:Start server PID: 21158
Forwarding everything to localhost:1025
Waiting for client on port: 1024
```

Start the client to send some messages to the server:
```
$ ./vulnserver_client.py 1024
Connecting to 127.0.0.1 port 1024
Send message 1
Send message 2
Send message 3
```

The server will print text similar to:
```
Client Thread0 started
INFO:root:Logging into: localhost:1025
Received from client: 0: 4
target: recv data
Received from server: 0: 2
Received from client: 0: 4
target: recv data
Received from server: 0: 2
Received from client: 0: 4
target: recv data
Received from server: 0: 2
target: recv data
ClientTcpThread terminating
Got 6 packets
```

Press `CTRL-C` to quit the server.

This will generate the file `in/data_0.pickle`. You can view it by using `../printpickly.py in/data_0.pickle`:

```
./ffw/vulnserver $ ../printpickle.py in/data_0.pickle
[   {   'data': 'AAAA', 'from': 'cli'},
    {   'data': 'ok', 'from': 'srv'},
    {   'data': 'BBBB', 'from': 'cli'},
    {   'data': 'ok', 'from': 'srv'},
    {   'data': 'CCCC', 'from': 'cli'},
    {   'data': 'ok', 'from': 'srv'}]
```

It should contain some data from server and client.


## Test intercepted data

Test if the recorded data can be replayed by using the test-mode. It will start the fuzz target, and replays the recorded data stored in `in/data_0.pickle` three times. If there are 0 fails, it is
pretty reproducible.

```
$ ./fuzzing.py test
Debug mode enabled
INFO:root:Using: TCP
INFO:root:Starting server with args: ['./ffw/vulnserver/bin/vulnserver_asan', '20000']
INFO:root:  Pid: 22247
INFO:root:Start server PID: 22247
==== Iteration =====
INFO:root:Open connection on localhost:20000
Handling msg: 0 Sending...
  Send: 4
Handling msg: 1 Receiving...
  Orig: 2
  Real: 2
Handling msg: 2 Sending...
  Send: 4
Handling msg: 3 Receiving...
  Orig: 2
  Real: 2
Handling msg: 4 Sending...
  Send: 4
Handling msg: 5 Receiving...
  Orig: 2
  Real: 2
==== Iteration =====
[...]
Itercount: 3
Fails:
Fails at msg #0: 0
Fails at msg #1: 0
Fails at msg #2: 0
Fails at msg #3: 0
Fails at msg #4: 0
Fails at msg #5: 0
```

All looking good!

## Perform fuzzing

We are ready to fuzz. Start the fuzzer:
```
$ ./fuzzing.py fuzz
Debug mode enabled
Config:  
  Running fuzzer:    Radamsa
  Outcomde dir:      ./ffw/vulnserver/out
  Target:            ./ffw/vulnserver/bin/vulnserver_asan
  Input dir:         ./ffw/vulnserver/in
  Analyze response:  True
Start child: 0

[...]

DEBUG:root:A fuzzing loop...
INFO:root:Open connection on localhost:20000
DEBUG:root:Fuzzing the data
DEBUG:root:selected input: 2  from: cli  len: 4
INFO:root:Call fuzzer, seed: 15032758009265251593
INFO:root:Send pre data:
DEBUG:root:  Sending pre message: 0
INFO:root:Send data:
DEBUG:root:  Sending message: 2
INFO:root:Could not read, crash?!
INFO:root: C Could not send, possible crash? (postdata)
INFO:root:Detected Crash (C)
INFO:root:getCrashData(): get data, but server alive?!
INFO:root:Get asan output: ./ffw/vulnserver/temp/asan.22379
INFO:root:Did not find ASAN output file: ./ffw/vulnserver/temp/asan.22379
INFO:root:Stop server PID: 22379
INFO:root:Starting server with args: ['./ffw/vulnserver/bin/vulnserver_asan', '20000']
INFO:root:  Pid: 22405
INFO:root:Start server PID: 22405
```

This will result in more and more files in the `out/` directory, if crashes are detected. Lets it run for a few minutes.
```
ffw/vulnserver$ ls out/
1071287157815228985.ffw   1147553628983128942.ffw   18287258929267146782.ffw
1071287157815228985.txt   1147553628983128942.txt   18287258929267146782.txt
10807046273026107559.ffw  15032758009265251593.ffw  2679312059348738636.ffw
10807046273026107559.txt  15032758009265251593.txt  2679312059348738636.txt
```

The txt files contain the plaintext information about the crash, the ffw
files are python pickle files.


## Verify crashes

We have a lot of crashes, as indicated by the files in the `out/` directory. Lets verify it to be
sure that they are indeed valid crashes, and get additional information about the crash:

```
ffw/vulnserver$ ./fuzzing.py verify
Debug mode enabled
INFO:root:Crash verifier
Processing 6 outcome files
Now processing: 0: ./ffw/vulnserver/out/15032758009265251593.ffw
INFO:root:Using: TCP
INFO:root:DebugServer: Start Server
DEBUG:root:START: ['./ffw/vulnserver/bin/vulnserver_asan', '21100']
INFO:root:Attach <PtraceProcess #23559> to debugger
INFO:root:Set <PtraceProcess #23559> options to 1
Listening on port: 20100
INFO:root:Server PID: 23559
INFO:root:DebugServer: Waiting for process event
INFO:root:Verifier: Server pid: 23559
New client connected
INFO:root:Server is ready (accepting connections)
INFO:root:Verifier: Sending fuzzed messages
INFO:root:Open connection on localhost:20100
[...]
```

If the crash from `out/` could be verified, new files appear in the `verfified/` directory:
```
ffw/vulnserver$ ls verified/
1071287157815228985.ffw  18287258929267146782.ffw  README.txt
1071287157815228985.txt  18287258929267146782.txt
```

## Replay crashes

To manually replay the crashes, e.g. if the target runs in GDB, use the
`replay` mode.

Start the target in a terminal in gdb:
```
dobin@unreal:~/Development/ffw/vulnserver$ gdb -q ./bin/vulnserver_asan
Reading symbols from ./bin/vulnserver_asan...(no debugging symbols found)...done.
(gdb) r 1024
Starting program: ./ffw/vulnserver/bin/vulnserver_asan 1024
Listening on port: 1024
```

In another terminal, use `replay` with a `.ffw` file:
```
dobin@unreal:~/Development/ffw/vulnserver$ ./fuzzing.py replay --port 1024 --file verified/18287258929267146782.ffw
Debug mode enabled
File: verified/18287258929267146782.ffw
Port: 1024
INFO:root:Using: TCP
INFO:root:Open connection on localhost:1024
INFO:root:ReceiveData err on msg 3: timed out
```

It should provoke the error in GDB:
```
New client connected
Received data with len: 4 on state: 0
Auth success
Received data with len: 28 on state: 1

Program received signal SIGSEGV, Segmentation fault.
0x000000004242b0b5 in ?? ()
```


## Honggmode

Honggmode uses hongfuzz for feedback driven fuzzing. It requires an up to date kernel and clang version. Tested on Ubuntu 17.04.

### Setup honggfuzz

Use the ffw-honggfuzz repository, and compile it:
```
git clone https://github.com/dobin/honggfuzz
make
make install
```

Specify location of honggfuzz in `fuzzing.py`:
```
"honggpath": "/home/fuzzer/honggfuzz/honggfuzz",
```

### Setup an open-source project

Compile target with:
```
export HFUZZ_CC_ASAN="true"
export CC=~/honggfuzz/hfuzz_cc/hfuzz-clang
```

### Setup a closed-source project

Add one of the following options. See https://github.com/google/honggfuzz/blob/master/docs/FeedbackDrivenFuzzing.md for reference. `--linux_perf_bts_edge` works well.

```
"honggmode_option": "--linux_perf_bts_edge"
"honggmode_option": "--linux_perf_ipt_block"
"honggmode_option": "--linux_perf_instr"
"honggmode_option": "--linux_perf_branch"
```

### Fuzz

Start with:
```
./fuzzing.py honggmode
```
Instead of `./fuzzing.py fuzz`




# Various infos

## Notes on (obsolete) python-ptrace

python-ptrace does not yield good results, and is currently disabled.

If you want to use `python-ptrace` in verifier mode, install it:
```
pip install pyinotify
```

And fix it.

### Fix ptrace

python-ptrace sometimes encounters a bug. Fix the regex specified below.
The path may be different (depending on how you installed pytohn-ptrace).
May not be always necessary (?). Will only affect verify-mode of ffw.

* Relevant file: memory_mapping.py
* Relevant part: PROC_MAP_REGEX

/usr/local/lib/python2.7/dist-packages/ptrace/debugger/memory_mapping.py
```
PROC_MAP_REGEX = re.compile(
    r'([0-9a-f]+)-([0-9a-f]+) '
    r'(.{4}) '
    r'([0-9a-f]+) '
    r'([0-9a-f]+):([0-9a-f]+) ' # replace orig line with this one
    r'([0-9]+)'
    r'(?: +(.*))?'
)
```


## Config

If in doubt:

```
sysctl net.core.somaxconn=4096
ulimit -c 999999
```

Or run as root.

## Compile targets

Use the following compile flags to increase bug detection rate
(with ASAN) and backtrace quality:
```
export CFLAGS="-fsanitize=address -fno-omit-frame-pointer"
```

# FAQ

## Can i fuzz windows binaries?

No.

## Can i fuzz closed source binaries?

Yes.
