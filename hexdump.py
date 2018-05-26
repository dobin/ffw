#!/usr/bin/env python3
# vim: set list et ts=8 sts=4 sw=4 ft=python:

# haklib.hexdump - convenient hexdumps
# Copyright (C) 2016, Daniel Roethlisberger <daniel@roe.ch>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Usage:
#
# from haklib.hexdump import hexdump_ex
# hexdump_ex(sys.stdin.read())

# https://github.com/droe/haklib/blob/master/hexdump.py

import binascii


def hexify(buf, sep=' '):
    return sep.join('%02x' % c for c in buf)


def hexdumpify(data):
    t = binascii.hexlify(data).decode('ascii')
    s = ' '.join(t[i:i + 2] for i in range(0, len(t), 2))
    return '\n'.join(s[i:i + 48] for i in range(0, len(s), 48))


def hexdump(data):
    print(hexdumpify(data))


def hexdumpify_ex(buf, length=16, replace='.'):
    FILTER = ''.join([(x > 0x1F and x < 0x7F) and chr(x) or replace for x in range(256)])
    lines = []
    for c in range(0, len(buf), length):
        bin = buf[c:c + length]
        hex = ' '.join(["%02x" % x for x in bin])
        if len(hex) > 24:
            hex = "%s %s" % (hex[:24], hex[24:])
        ascii = ''.join(["%s" % ((x <= 127 and FILTER[x]) or replace) for x in bin])
        lines.append("%08x:  %-*s  |%s|\n" % (c, length * 3, hex, ascii))
    return ''.join(lines)


def hexdump_ex(buf, length=16, replace='.'):
    print(hexdumpify_ex(buf, length, replace))
