#!/usr/bin/python

import sys


class AsanParser:
    def __init__(self):
        self.lines = None


    def loadData(self, data):
        self.lines = [s.strip() for s in data.splitlines()]


    def loadFile(self, filename):
        f = open(filename, "r")
        asanData = f.read()
        f.close()

        # split data into lines
        self.lines = [s.strip() for s in asanData.splitlines()]


    def getAsanData(self):
        asanData = {
            "cause": "N/A",
            "cause_line": "N/A",
            "pc": 0x0,
        }

        if not self.lines:
            return asanData

        # first line is just some ===, the second line is the important one
        headerLine = self.lines[1]

        if "heap-buffer-overflow" in headerLine:
            asanData["cause"] = "Heap BoF"

        if "attempting double-free" in headerLine:
            asanData["cause"] = "DoubleFree"


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
        mainLine = line.split(" ")
        asanData["pc"] = mainLine[1]
        asanData["cause_line"] = mainLine[3] + " " + mainLine[4]

        # backtrace
        # typical:
        # "#0 0x7fb6e9cddb60 in __interceptor_free (/usr/lib/x86_64-linux-gnu/libasan.so.3+0xc6b60)"
        # "#1 0x55f0dffae17a in mg_mqtt_destroy_session ../../mongoose.c:10445"
        # "#2 0x55f0dffae1ad in mg_mqtt_close_session ../../mongoose.c:10451"
        # "#3 0x55f0dffaf162 in mg_mqtt_broker ../../mongoose.c:10587"
        bt = ""
        end = n + 5
        while n < end:
            lineSplit = self.lines[n].split(" ")
            bt += lineSplit[3] + " " + lineSplit[4] + "\n"
            n += 1
        asanData["backtrace"] = bt

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
        entry["pc"] = asanData["pc"]
        entry["backtrace"] = asanData["backtrace"]
    else:
        entry["cause"] = "n/a"
        entry["cause_line"] = "n/a"
        entry["pc"] = entry["codebase"]
        entry["backtrace"] = "n/a"


if __name__ == '__main__':
    sys.exit(main())
