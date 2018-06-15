# Honggmode

Honggmode uses hongfuzz for feedback driven fuzzing. It requires an up to date kernel and clang version. Tested on Ubuntu 17.04 and Ubuntu 17.10.

Note: This tutorial is based on successful completion of
[Setup the sample project tutorial](https://github.com/dobin/ffw/blob/master/docs/tutorial-sample-project.md)

## Install honggfuzz

Use the honggfuzz repository, and compile it:
```
$ cd
$ git clone https://github.com/google/honggfuzz
$ make
```

Note: In Ubuntu 17.10, this requires the following packages:
```
$ sudo apt-get install binutils-dev libunwind-dev clang
```


## Fuzz with software-based feedback

Note:
* This required Ubuntu 17.04 or higher
* On Ubuntu 16.04 there will be something like `clang: error: unsupported argument 'trace-pc-guard' to option 'fsanitize-coverage='`

Compile target with `hfuzz_cc/hfuzz-clang` or similar.

Compile `vulnserver` with hfuzz:
```
ffw/vulnserver/src# make
gcc -g -O0 -fsanitize=address -fno-stack-protector -fno-omit-frame-pointer vulnserver.c -o vulnserver_plain_asan
gcc -g -O0 -fno-stack-protector -fno-omit-frame-pointer vulnserver.c -o vulnserver_plain

ffw/vulnserver/src# cp vulnserver_hfuzz ../bin
```

Change `config.py` to point to this new binary:
```
"target_bin": "bin/vulnserver_hfuzz",
```

Start in honggmode:
```
ffw/vulnserver/# ../ffw.py --honggmode
Basedir: /Development/ffw
Config file: /Development/ffw/vulnserver/config.py
Rember "use_netnamespace requires nesting in container"
Start fuzzing child #0
 connected to honggfuzz!
Performing warmup. This can take some time.
    Corpus   0  (    -):  Parent:   -  Msg:   -  Children:   0  Crashes:   0
    Corpus   1  (    -):  Parent:   -  Msg:   -  Children:   0  Crashes:   0
Found crash!
Found crash!
Found crash!
Found crash!
Found crash!
Found crash!
Found crash!
    Corpus   0  (    -):  Parent:   -  Msg:   -  Children:   0  Crashes:   5
    Corpus   1  (    -):  Parent:   -  Msg:   -  Children:   0  Crashes:   2
Found crash!
Found crash!
Found crash!
    Corpus   0  (    -):  Parent:   -  Msg:   -  Children:   0  Crashes:   5
    Corpus   1  (    -):  Parent:   -  Msg:   -  Children:   0  Crashes:   5
Found crash!
Found crash!
Found crash!
Found crash!
    Corpus   0  (    -):  Parent:   -  Msg:   -  Children:   0  Crashes:   8
    Corpus   1  (    -):  Parent:   -  Msg:   -  Children:   0  Crashes:   6
Found crash!
Found crash!
^CFinished
```


## Test the honggfuzz integration mode

### Compile

Compile target with:
```
$ cd ~/honggfuzz/socketfuzzer
$ export HFUZZ_CC_ASAN="true"
$ export CC=~/honggfuzz/hfuzz_cc/hfuzz-clang
$ ~/honggfuzz/hfuzz_cc/hfuzz-clang vulnserver_cov.c -o vulnserver_cov
```

Start honggfuzz with the following command line on port 5001:
```
~/honggfuzz/honggfuzz  --keep_output --debug --sanitizers --sancov --stdin_input --threads 1 --verbose --logfile log.txt --socket_fuzzer -- ./vulnserver_cov 5001
Waiting for SocketFuzzer connection on socket: /tmp/honggfuzz_socket
```

On another terminal, connect:
```
$ python honggfuzz_socketclient.py auto
connecting to /tmp/honggfuzz_socket
--[ Adding file to corpus...
--[ Target crashed
--[ Adding file to corpus...
--[ Target crashed
--[ Adding file to corpus...
--[ Target crashed
--[ Target crashed
--[ Adding file to corpus...
--[ Adding file to corpus...
--[ Target crashed
--[ Target crashed
--[ Target crashed
--[ Target crashed
--[ Target crashed
--[ Target crashed
```

If the message `Adding file to corpus` appears, it works.
