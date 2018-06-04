#!/usr/bin/env python2

import logging
import hexdump
import subprocess


"""
Several utility functions.
"""


# https://stackoverflow.com/questions/11602386/python-function-for-capping-a-string-to-a-maximum-length
def cap(s, l):
    return s if len(s) <= l else s[0:l - 3] + '...'


def filenameWithoutExtension(file_name):
    if '.' in file_name:
        separator_index = file_name.rindex('.')
        base_name = file_name[:separator_index]
        return base_name
    else:
        return file_name


def xstr(s):
    if s is None:
        return '-'
    return str(s)


def shortSeed(s):
    if s is None:
        return '-'

    return s[:4]


def setupSlaveLoggingWithFile(threadId):
    f = 'ffw-debug-slave-' + str(threadId) + '.log'

    fileh = logging.FileHandler(f, 'a')
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    fileh.setFormatter(formatter)

    log = logging.getLogger()  # root logger
    for hdlr in log.handlers[:]:  # remove all old handlers
        log.removeHandler(hdlr)
    log.addHandler(fileh)      # set the new handler

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.WARN)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)


def hexdumpc(str):
    hexdump.hexdump_ex( bytearray(str) )


def setupTmpfs(config, enable=True):
    if enable:
        logging.info("Mounting tmpfs")
        cmd = [ "/bin/mount", "-t", "tmpfs", "tmpfs", config['temp_dir'] ]
        subprocess.call(cmd)
    else:
        logging.info("UnMounting tmpfs")
        cmd = [ "/bin/umount", config['temp_dir'] ]
        subprocess.call(cmd)
