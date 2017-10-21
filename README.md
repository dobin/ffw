# FFW - Fuzzing For Worms

Fuzzes network servers.

* A network server which does not fork and accepts a port on the command line

# Install

## get ffw 

```
git clone https://github.com/dobin/ffw.git
cd ffw/
```

## Install deps

```
pip install python-ptrace
```

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
    r'([0-9a-f]+):([0-9a-f]+) ' ##### this line needs to be fixed 
    r'([0-9]+)'
    r'(?: +(.*))?'
)
```

## install radamsa

Default path specified in ffw for radamsa is `ffw/radamsa`:

```
$ git clone https://github.com/aoh/radamsa.git
$ cd radamsa
$ make
```

# Setup first project

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


## Create directory structure 

Create a copy of the template directory for the software you want to test, in this case vulnserver:

```
cp -R template/ vulnserver/
cd vulnserver/
```

The directory `vulnserver` will be our working directory from now on. 
It will contain the file `fuzzing.py`, and the directories `in`, `bin`, `out`, `verified`, and `temp`.

## Copy binary

Copy the binary of the server you want to fuzz to bin, e.g.:
```
cd /tmp/vulnserver/
make
cp vulnserver /path/to/ffw/vulnserver/bin
```

## Configure fuzzer

Edit fuzzing.py until STOP line. Specify the path to the binary, and how to give 
```
    "name": "vulnserver",
    "target_bin" : PROJDIR + "bin/vulnserver",
    "target_args": "--port %(port)i",
    "ipproto": "tcp",
    "debug": True,
```

## Perform intercept

Start interceptor-mode. You can use the original standard port of the server as argument.
Port+1 will be used for the real server port:
```
./fuzzing.py interceptor 1024
```

Start the client and send some messages to the server:
```
start client
```

The server will print text similar to:
```
```

This will generate the file `in/data_0.pickle". You can view it by using `../printpickly.py in/data_0.pickle`.
```
printpickle data0 output
```

## Verify intercepted data

Verify if the recorded data can be replayed by using the test-mode. It will start the fuzz target,
and replays the recorded data storedin `in/data_0.pickle` three times. If there are 0 fails, it is 
pretty reproducible. 


```
verify output
```

## Perform fuzzing

We are ready to fuzz. Start the fuzzer:
```
fuzz
```

This will result in more and more files in the `out/` directory, if crashes are detected:
```
```


## Verify crashes

We have a lot of crashes, as indicated by the files in the `out/` directory. Lets verify it to be 
sure that they are indeed valid crashes, and get additional information about the crash:

```
verify
```

If the crash from `out/` could be verified, new files appear in the `verfified/` directory:
```
asdf
```


# Detailed Modes Description

* Interceptor
* Tester
* Fuzzer
* Verifier
* Replayer

<tbd>


# Various infos

## Config

```
sysctl net.core.somaxconn=4096
ulimit -c 999999
```

## Compile targets

Use:
```
export CFLAGS="-fsanitize=address -fno-omit-frame-pointer"
```

# FAQ

## Can i fuzz windows binaries?

No

## Can i fuzz closed source binaries?

Yes

