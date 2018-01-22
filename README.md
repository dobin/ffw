# FFW - Fuzzing For Worms

Fuzzes network servers/services by intercepting valid network
communication data, then replay it with some fuzzing.

FFW can fuzz open source applications, and also closed
source applications. It also supports feedback driven fuzzing
by instrumenting honggfuzz, for both open- and closed source apps. 

In comparison with the alternatives, FFW is the most advanced, 
feature-complete and tested network fuzzer.

Features:
* Fuzzes all kind of network protocol (HTTP, MQTT, SMTP, you name it)
* No modification of the fuzzing target needed (at all)
* Can fuzz open- and closed-source projects
* Has feedback-driven fuzzing (with compiler support, or hardware based)
* Can fuzz network clients too (wip)
* Fast fuzzing setup (no source code changes or protocol reversing needed!)
* Reasonable fuzzing performance

# Installation

## Get FFW

```
git clone https://github.com/dobin/ffw.git
cd ffw/
```

## Install FFW dependencies

```
pip install -r requirements.txt
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
* [Setup the Grammar based fuzzer](https://github.com/dobin/ffw/blob/master/docs/tutorial-grammar-based.md)
* [Setup the feedback-driven fuzzing project tutorial](https://github.com/dobin/ffw/blob/master/docs/tutorial-honggmode.md)
* [Some fuzzing help and infos](https://github.com/dobin/ffw/blob/master/docs/notes.md)

# Alternatives 

## Fuzzotron

Available via https://github.com/denandz/fuzzotron. "Fuzzotron is a simple network fuzzer supporting TCP, UDP and multithreading."

Support network fuzzing, also uses Radamsa. Can use coverage data, but it is experimental.

Con's:
* Does not restart target server
* Unreliable crash detection
* Experimental code coverage

## Mutiny

Available via https://github.com/Cisco-Talos/mutiny-fuzzer. "The Mutiny Fuzzing Framework is a network fuzzer that operates by replaying PCAPs through a mutational fuzzer."

Con's: 
* No code coverage
* Only one commit (no development?)
* Rudimentary crash detection

# FAQ

## Can i fuzz windows binaries?

No.

## Can i fuzz closed source binaries?

Yes.
