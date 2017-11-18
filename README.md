# FFW - Fuzzing For Worms

Fuzzes network servers/services by intercepting valid network
communication data, then replay it with some fuzzing.

FFW can fuzz open source applications, and also closed
source applications. It also supports feedback driven fuzzing
by instrumenting honggfuzz, for both open- and closed source apps. This is called `honggmode`.

Features:
* Fuzzes all kind of network protocol (-server)
* No modification of the fuzzing target needed (at all)
* Can fuzz open- and closed-source projects
* Has feedback-driven fuzzing (compiler support, or hardware based)
* Can fuzz network clients too (wip)
* Very fast fuzzing setup, no source code changes or protocol reversing needed!


# Installation

## Install dependencies

```
pip install pyinotify psutil python-ptrace requests hexdump
```

## Get ffw

```
git clone https://github.com/dobin/ffw.git
cd ffw/
```

## Install Radamsa fuzzer

```
$ git clone https://github.com/aoh/radamsa.git
$ cd radamsa
$ make
```

Default Radamsa directory specified in ffw is `ffw/radamsa`.

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


For a step-by-step guide:
* [Setup the sample project tutorial](https://github.com/dobin/ffw/blob/master/docs/tutorial-sample-project.md)
* [Setup the feedback-driven fuzzing project tutorial](https://github.com/dobin/ffw/blob/master/docs/tutorial-honggmode.md)


# FAQ

## Can i fuzz windows binaries?

No.

## Can i fuzz closed source binaries?

Yes.
