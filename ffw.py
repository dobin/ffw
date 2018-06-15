#!/usr/bin/env python2

import framework

import sys

"""
The first way to use FFW is to create a subdirectory in ffw/, and then
copy the fuzzing.py from template/

This is kinda suboptimal, so this ffw.py is able to read a config file
similar to fuzzing.py instead.
"""


def main():
    framework.realMain(None)


if __name__ == '__main__':
    sys.exit(main())
