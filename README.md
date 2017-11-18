# FFW - Fuzzing For Worms

Fuzzes network servers/services by intercepting valid network
communication data, then replay it with some fuzzing.

FFW can fuzz open source applications, and also closed
source applications. It also supports feedback driven fuzzing
by instrumenting honggfuzz, for both open- and closed source apps. This is called `honggmode`.

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


For a step-by-step guide:
* [Setup the sample project tutorial](https://github.com/dobin/ffw/blob/master/docs/tutorial-sample-project.md)
* [Setup the feedback-driven fuzzing project tutorial](https://github.com/dobin/ffw/blob/master/docs/tutorial-honggmode.md)


# FAQ

## Can i fuzz windows binaries?

No.

## Can i fuzz closed source binaries?

Yes.
