# FFW: Setup sample project

## Create directory structure

Create a copy of the template directory for the software you want to test, in this case vulnserver:

```
$ cd ffw/
$ cd vulnserver/
$ cp -R ../template/* .
```

The directory `vulnserver` will be our working directory from now on.
It will contain the file `fuzzing.py`, and the directories `in/`, `bin/`, `out/`, `verified/`, and `temp/`.


## Compile the target

Copy the binary of the server you want to fuzz to bin. It is already prepared in the `src/` directory, can be compiled with `make`:
```
ffw/vulnserver/ $ cd src
ffw/vulnserver/src $ make
gcc -O0 -fsanitize=address -fno-stack-protector -fno-omit-frame-pointer vulnserver.c -o vulnserver_asan
gcc -O0 -fno-stack-protector -fno-omit-frame-pointer vulnserver.c -o vulnserver_plain
```

And copy it to the `bin/` directory:
```
ffw/vulnserver/src $ cp ./vulnserver_plain_asan ./bin
```

## Configure fuzzer

Edit `fuzzing.py` until STOP line. Specify the path to the binary, and how to give the port number as parameter:
```
    "name": "vulnserver 1",
    "target_bin" : PROJDIR + "bin/vulnserver_plain_asan",
    "target_args": "%(port)i",
    "ipproto": "tcp",
```


## Perform intercept

Start interceptor-mode. By default it will take port 10'000 as default listener
port, and starts the target server on port 20'000.
```
/ffw/vulnserver# ../ffw.py --intercept --debug
Basedir: /Development/ffw
Config file: /Development/ffw/vulnserver/config.py
Interceptor listen on port: 10000
Target server port: 20000
INFO:root:Starting server with args: ['/Development/ffw/vulnserver/bin/vulnserver_plain_asan', '20000']
INFO:root:  Pid: 12908
INFO:root:  Return code: None
INFO:root:Start server PID: 12908
INFO:root:Using: TCP
INFO:root:NET Check if we can connect to server localhost:20000
DEBUG:root:NET testServerConnectionTcp: connect to ('localhost', 20000)
INFO:root:Interceptor: Forwarding everything to localhost:20000
INFO:root:Interceptor: Waiting for new client on port: 10000
```

Start the client in another terminal to send some messages to the server:
```
ffw/vulnserver# ./src/vulnserver_client.py 10000
Connecting to 127.0.0.1 port 10000
Send message 1
Send message 2
Send message 3

```

The server will print text similar to:
```
Interceptor: Got new client
INFO:root:Interceptor TCP Thread: Client Thread0 started
INFO:root:Interceptor TCP Thread: Logging into: localhost:20000
INFO:root:Interceptor TCP Thread: Received from client: 0: 4
INFO:root:Interceptor TCP Thread: target: recv data
INFO:root:Interceptor TCP Thread: Received from server: 0: 2
INFO:root:Interceptor TCP Thread: Received from client: 0: 4
INFO:root:Interceptor TCP Thread: target: recv data
INFO:root:Interceptor TCP Thread: Received from server: 0: 2
INFO:root:Interceptor TCP Thread: Received from client: 0: 4
INFO:root:Interceptor TCP Thread: target: recv data
INFO:root:Interceptor TCP Thread: Received from server: 0: 2
INFO:root:Interceptor TCP Thread: target: recv data
INFO:root:Interceptor TCP Thread: ClientTcpThread terminating
INFO:root:Interceptor TCP Thread: Got 6 packets
Interceptor TCP Thread: Storing into file: intercept0.pickle
DEBUG:root:Write corpus to file: /Development/ffw/vulnserver/corpus/intercept0.pickle
```

Press `CTRL-C` to quit the server.

This will generate the file `corpus/intercept0.pickle`. You can view it by using `../printpickly.py corpus/intercept0.pickle`:

```
ffw/vulnserver $ ../printpickle.py corpus/intercept0.pickle
[   {   'data': 'AAAA', 'from': 'cli'},
    {   'data': 'ok', 'from': 'srv'},
    {   'data': 'BBBB', 'from': 'cli'},
    {   'data': 'ok', 'from': 'srv'},
    {   'data': 'CCCC', 'from': 'cli'},
    {   'data': 'ok', 'from': 'srv'}]
```

It should contain some data from server and client.


## Test intercepted data

Test if the recorded data can be replayed by using the test-mode. It will start the fuzz target, and replays the recorded data stored in `corpus/intercept0.pickle` several times. If there are 0 fails, it is
pretty reproducible.

```
ffw/vulnserver# ../ffw.py --test
Basedir: /Development/ffw
Config file: /Development/ffw/vulnserver/config.py
Using port: 20000
Initial test successful - could connect to server.
---[ Testing CorpusData: data_0.pickle 32 times
We use the following recvTimeout: 0.03
No timeouts, looking fine!
---[ Testing CorpusData: intercept0.pickle 32 times
We use the following recvTimeout: 0.03
No timeouts, looking fine!
```

All looking good!

## Perform fuzzing

We are ready to fuzz. Start the fuzzer:
```
ffw/vulnserver# ../ffw.py --fuzz --debug
Basedir: /Development/ffw
Config file: /Development/ffw/vulnserver/config.py
Rember "use_netnamespace requires nesting in container"
INFO:root:Mounting tmpfs
DEBUG:root:Read corpus from file: /Development/ffw/vulnserver/corpus/data_0.pickle
DEBUG:root:Read corpus from file: /Development/ffw/vulnserver/corpus/intercept0.pickle
INFO:root:Input corpus files loaded: 2
Start child: 0
Thread#  Fuzz/s   Count   Crashes
DEBUG:nsenter:Entering net namespace /var/run/netns/ffw-0
INFO:root:Setup fuzzing..
DEBUG:root:Read corpus from file: /Development/ffw/vulnserver/corpus/data_0.pickle
DEBUG:root:Read corpus from file: /Development/ffw/vulnserver/corpus/intercept0.pickle
INFO:root:Input corpus files loaded: 2
INFO:root:Using: TCP
INFO:root:Starting server with args: ['/Development/ffw/vulnserver/bin/vulnserver_plain_asan', '20000']
INFO:root:  Pid: 12932
INFO:root:  Return code: None
INFO:root:Start server PID: 12932
DEBUG:root:NET testServerConnectionTcp: connect to ('localhost', 20000)
INFO:root:NET Server is ready (accepting connections)
0 Start fuzzing...
DEBUG:root:


DEBUG:root:A fuzzing loop...
INFO:root:NET Open connection on localhost:20000
DEBUG:root:Fuzz the data
INFO:root:Call mutator, seed: 17050315392402380266
DEBUG:root:Mutator command args: -s 17050315392402380266 -o /Development/ffw/vulnserver/temp/17050315392402380266.out.raw "/Development/ffw/vulnserver/temp/17050315392402380266.in.raw"
DEBUG:root:Read fuzzing data: BBBBBBBBBBBBB
INFO:root:NET Send pre data:
DEBUG:root:NET  Sending pre message: 0
DEBUG:root:Sending: AAAA
DEBUG:root:Received: ok
INFO:root:NET Send data:
DEBUG:root:NET   Sending fuzzed message: 2
DEBUG:root:Sending: BBBBBBBBBBBBB
INFO:root:NET ReceiveData err on msg 3: timed out
INFO:root: C Could not send, possible crash? (postdata)
DEBUG:root:NET testServerConnectionTcp: connect to ('localhost', 20000)
INFO:root:C Broken connection... continue
DEBUG:root:
[...]
```

This will result in more and more files in the `crashes/` directory, if crashes are detected. Lets it run for a few minutes.

```
ffw/vulnserver# ls crashes/
data_0.5329_2.5329_2.crash  intercept0.1240_2.1240_2.crash
data_0.9988_4.9988_4.crash  intercept0.1647_4.1647_4.crash
```

Lets have a look at a content of a crash file:
```
ffw/vulnserver# ../printpickle.py crashes/data_0.3975_4.3975_4.crash
{   'asanOutput': '=================================================================\n==12983==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x6020000000b8 at pc 0x7f59ef30b77a bp 0x7fff42b67050 sp [...]\n',
    'corpusData': {   'filename': 'data_0.3975_4.pickle',
                      'fuzzer': 'Radamsa',
                      'networkData': [   {   'data': 'AAAA',
                                             'from': 'cli',
                                             'index': 0,
                                             'latency': None,
                                             'timeouts': 0},
                                         {   'data': 'ok',
                                             'from': 'srv',
                                             'index': 1,
                                             'latency': 0.0002589225769042969,
                                             'timeouts': 0},
                                         {   'data': 'BBBB',
                                             'from': 'cli',
                                             'index': 2,
                                             'latency': None,
                                             'timeouts': 0},
                                         {   'data': 'ok',
                                             'from': 'srv',
                                             'index': 3,
                                             'latency': 0.00014591217041015625,
                                             'timeouts': 0},
                                         {   'data': 'C\xf3\xa0\x81\xe7C\xf3\xa0\x81\xa7\xe2\x80\x86Cc',
                                             'from': 'cli',
                                             'index': 4,
                                             'isFuzzed': True,
                                             'latency': None,
                                             'timeouts': 0},
                                         {   'data': 'ok',
                                             'from': 'srv',
                                             'index': 5,
                                             'latency': None,
                                             'timeouts': 1}],
                      'parentFilename': 'data_0.pickle',
                      'seed': '3975385818332432263',
                      'time': None},
    'exitcode': 0,
    'filename': 'data_0.3975_4.3975_4.crash',
    'fuzzerPos': 'A',
    'reallydead': -6,
    'serverpid': 12983,
    'signum': 0}
```


## Verify crashes

We have a lot of crashes, as indicated by the files in the `crashes/` directory. Lets verify it to be sure that they are indeed valid crashes, and get additional information about the crash:

```
ffw/vulnserver# ../ffw.py --verify
Basedir: /Development/ffw
Config file: /Development/ffw/vulnserver/config.py
06-15 10:42 root         WARNING  Terminate <PtraceProcess #13014>
Verifier: crash verified: data_0.5329_2.5329_2.crash: 140161457819835
Verifier: crash verified: data_0.5329_2.5329_2.crash: None
06-15 10:42 root         WARNING  Terminate <PtraceProcess #13027>
Verifier: crash verified: intercept0.1647_4.1647_4.crash: 139923769520315
Verifier: crash verified: intercept0.1647_4.1647_4.crash: None
06-15 10:42 root         WARNING  Terminate <PtraceProcess #13040>
Verifier: crash verified: data_0.9988_4.9988_4.crash: 140067457188027
Verifier: crash verified: data_0.9988_4.9988_4.crash: None
06-15 10:42 root         WARNING  Terminate <PtraceProcess #13053>
Verifier: crash verified: intercept0.1240_2.1240_2.crash: 139797202968763
Verifier: crash verified: intercept0.1240_2.1240_2.crash: None
06-15 10:42 root         WARNING  Terminate <PtraceProcess #13066>
Verifier: crash verified: data_0.3975_4.3975_4.crash: 140396065943739
Verifier: crash verified: data_0.3975_4.3975_4.crash: None
```

If the crash from `crashes/` could be verified, new files appear in the `verfified/` directory:
```
ffw/vulnserver# ls verified/
README.txt                            data_0.9988_4.9988_4.gdb.verified
data_0.3975_4.3975_4.asan.verified    data_0.9988_4.9988_4.ptrace.verified
data_0.3975_4.3975_4.gdb.verified     intercept0.1240_2.1240_2.asan.verified
data_0.3975_4.3975_4.ptrace.verified  intercept0.1240_2.1240_2.gdb.verified
data_0.5329_2.5329_2.asan.verified    intercept0.1240_2.1240_2.ptrace.verified
data_0.5329_2.5329_2.gdb.verified     intercept0.1647_4.1647_4.asan.verified
data_0.5329_2.5329_2.ptrace.verified  intercept0.1647_4.1647_4.gdb.verified
data_0.9988_4.9988_4.asan.verified    intercept0.1647_4.1647_4.ptrace.verified
```

The `.verified` pickle file will have a lot of additional information
about the crash.


## Replay crashes

To manually replay the crashes, e.g. if the target runs in GDB, use the
`replay` mode.

Start the target in a terminal in gdb:
```
ffw/vulnserver# gdb -q ./bin/vulnserver_plain_asan
Reading symbols from ./bin/vulnserver_plain_asan...done.
(gdb) r 20000
Starting program: /Development/ffw/vulnserver/bin/vulnserver_plain_asan 20000
[Thread debugging using libthread_db enabled]
Using host libthread_db library "/lib/x86_64-linux-gnu/libthread_db.so.1".
Listening on port: 20000
```

In another terminal, use `replay` with either the crash or verified file:
```

```

It should provoke the crash in the target program running in GDB:
```
New client connected
Received data with len: 4 on state: 0
Auth success
Received data with len: 4 on state: 1
BBBB
Received data with len: 15 on state: 2
=================================================================
==13085==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x602000000018 at pc 0x7ffff6e9377a bp 0x7fffffffde90 sp 0x7fffffffd638
[...]
```
