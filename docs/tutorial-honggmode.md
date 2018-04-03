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

## Fuzz with hardware-based feedback

Note:
* Requires a new CPU, Kernel
* Does not work in vmware
* Requires root

Go into the vulnserver ffw project:

```
$ cd ~/ffw/vulnserver
```

Edit the `fuzzing.py` and specify that we want to perform hardware-based
fuzzing feedback:

```
"honggpath": "/home/fuzzer/honggfuzz/honggfuzz",
"honggcov": "hw"
```

We will still use "vulnserver_asan" as binary, which is not compiled with
any fuzzing feedback code.

Start with:
```
# ./fuzzing.py --honggmode --debug
```
(Instead of `./fuzzing.py --fuzz`)

You'll should have an output like this if it works:
```
INFO:root:--[ Adding file to corpus...
```

## Fuzz with software-based feedback

Note:
* This required Ubuntu 17.04 or higher
* On Ubuntu 16.04 there will be something like `clang: error: unsupported argument 'trace-pc-guard' to option 'fsanitize-coverage='`

Compile `vulnserver` with hfuzz:
```
$ cd vulnserver/
$ export HFUZZ_CC_ASAN="true"
$ ~/honggfuzz/hfuzz_cc/hfuzz-clang vulnserver.c -o bin/vulnserver_hfuzz
```

Change config to point to this new binary:
```
"target_bin": PROJDIR + "bin/vulnserver_hfuzz",
```

Configure honggfuzz:
```
"honggpath": "/home/fuzzer/honggfuzz/honggfuzz",
"honggmode_option": "sw"
```

Start honggfuzz:
```
$ ./fuzzing.py --honggmode --debug
```

You'll should have an output like this if it works:
```
INFO:root:--[ Adding file to corpus...
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

### Closed-source project options

Add one of the following options. See https://github.com/google/honggfuzz/blob/master/docs/FeedbackDrivenFuzzing.md for reference. `--linux_perf_bts_edge` works well.

```
"honggmode_option": "--linux_perf_bts_edge"
"honggmode_option": "--linux_perf_ipt_block"
"honggmode_option": "--linux_perf_instr"
"honggmode_option": "--linux_perf_branch"
```
