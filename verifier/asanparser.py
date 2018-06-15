#!/usr/bin/python

import sys
import re
import logging

from servercrashdata import ServerCrashData


class AsanParser(object):
    """
    Parses ASAN output files.

    If a binary is compiled with ASAN, it will/should create output or file
    which contains detailed information about the vulnerability and crash.

    This class attempts to parse this text file and to extract all
    necessary information, e.g. the fault instruction.
    """

    def __init__(self):
        self.lines = None
        self.data = None


    def loadData(self, data):
        self.data = data
        self.lines = [s.strip() for s in data.splitlines()]


    def loadFile(self, filename):
        f = open(filename, "r")
        asanData = f.read()
        f.close()

        logging.info("ASAN: " + asanData)
        print(asanData)

        # split data into lines
        self.lines = [s.strip() for s in asanData.splitlines()]
        self.data = asanData


    def getAsCrashData(self):
        asanData = self.getAsanData()
        crashData = ServerCrashData(
            backtrace=asanData["backtrace"],
            cause=asanData["cause"],
            analyzerOutput=self.data,
            faultAddress=asanData["faultAddress"],
            analyzerType='asan',
        )
        return crashData


    def getAsanData(self):
        asanData = {
            "cause": "N/A",
            "cause_line": "N/A",
            "faultAddress": 0x0,
            "backtrace": None,
        }

        if not self.lines:
            return asanData

        logging.debug("ASANdata: " + str(self.lines))

        # first line is just some ===, the second line is the important one
        headerLine = self.lines[1]

        if "heap-buffer-overflow" in headerLine:
            asanData["cause"] = "Heap BoF"

        if "attempting double-free" in headerLine:
            asanData["cause"] = "DoubleFree"

        if "heap-use-after-free" in headerLine:
            asanData["cause"] = "UaF"

        if "memcpy-param-overlap" in headerLine:
            asanData["cause"] = "Memcpy"

        # find "^#1"
        # #0 is usually the asan line where it failed, which does not interest us
        n = 0
        line = None
        while n < len(self.lines):
                line = self.lines[n]
                if line.startswith("#0"):
                        break
                n += 1

        if "libasan.so" in line:
            n += 1
            line = self.lines[n]


        # split that main line
        # "==58842==ERROR: AddressSanitizer: heap-buffer-overflow on address
        #   0x60200000eed8 at pc 0x7f2c3ac7b033 bp 0x7ffd1e7630f0 sp 0x7ffd1e762898"
        # or
        # ==1996==ERROR: AddressSanitizer: memcpy-param-overlap: memory ranges
        #   [0x7ffe1a3fd0e0,0x7ffe1a3fd4a5) and [0x7ffe1a3fd190, 0x7ffe1a3fd555) overlap
        mainLine = headerLine.split(" ")
        logging.info("Mainline: " + str(mainLine))

        # #1 0x55b23bee8491 in handleData1 /Development/ffw/vulnserver/vulnserver.c:20
        tmp = line.split(" ")
        asanData["faultAddress"] = int(tmp[1], 16)
        asanData["cause_line"] = "neh"


        # backtrace
        # typical:
        # "#0 0x7fb6e9cddb60 in __interceptor_free (/usr/lib/x86_64-linux-gnu/libasan.so.3+0xc6b60)"
        # "#1 0x55f0dffae17a in mg_mqtt_destroy_session ../../mongoose.c:10445"
        # "#2 0x55f0dffae1ad in mg_mqtt_close_session ../../mongoose.c:10451"
        # "#3 0x55f0dffaf162 in mg_mqtt_broker ../../mongoose.c:10587"
        # new:
        # "#0 0x55b0a2 (/home/dobin/ffw/mongoose_mqtt_69/bin/mqtt_broker+0x55b0a2)"
        # "#1 0x55cf04 (/home/dobin/ffw/mongoose_mqtt_69/bin/mqtt_broker+0x55cf04)"
        # "#2 0x55c793 (/home/dobin/ffw/mongoose_mqtt_69/bin/mqtt_broker+0x55c793)"
        btStr = ""
        btArr = []
        # n already defined
        while n < len(self.lines):
            lineSplit = self.lines[n].split(" ")
            if len(lineSplit) <= 3:
                n += 1
                continue
            bt = lineSplit[2] + " " + lineSplit[3]

            # remove most of the path
            bt = re.sub(r'/.*/', "", bt)

            btStr += bt + "\n"
            btArr.append(bt)
            n += 1
        asanData["backtrace"] = btArr

        return asanData


def main():
    filename = "./asan.txt"
    hasAsan = True
    entry = {}

    if hasAsan:
        asanParser = AsanParser()
        asanParser.loadFile(filename)
        asanData = asanParser.getAsanData()

        entry["cause"] = asanData["cause"]
        entry["cause_line"] = asanData["cause_line"]
        entry["faultAddress"] = asanData["faultAddress"]
        entry["backtrace"] = asanData["backtrace"]
    else:
        entry["cause"] = "n/a"
        entry["cause_line"] = "n/a"
        entry["faultAddress"] = entry["codebase"]
        entry["backtrace"] = "n/a"


if __name__ == '__main__':
    sys.exit(main())
