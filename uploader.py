#!/usr/bin/env python2

import os
import glob
import requests
import json
import sys
import base64
import time
import pprint

import utils


class Uploader(object):
    def __init__(self, config, server, user, password):
        self.config = config

        self.projectId = None
        if server is None:
            self.server = "http://localhost:8000"
        else:
            self.server = server

        self.user = user
        self.password = password
        self.auth = ()

        if self.user is not None and self.password is not None:
            self.auth = (self.user, self.password)
            print "AUTH: " + str(self.auth)



    def uploadVerifyDir(self):
        outcomesDir = os.path.abspath(self.config["verified_dir"])
        outcomesFiles = glob.glob(os.path.join(outcomesDir, '*.ffw'))

        print("Processing %d outcome files" % len(outcomesFiles))

        if not self.projectExistsInCloud():
            self.createProjectInCloud()

        for outcomeFile in outcomesFiles:
            print "Process: " + outcomeFile
            data = utils.readPickleFile(outcomeFile)

            if data is not None:
                self.uploadData(data)

            time.sleep(0.1)


    def projectExistsInCloud(self):
        payload = {'name': self.config["name"]}
        url = self.server + "/api/projects/"
        r = requests.get(url, params=payload, auth=self.auth)

        print "Code: " + str(r.status_code)
        if r.status_code != 200:
            print "R: " + r.text
            sys.exit(0)
        j = r.json()

        if not j:
            return False

        j = j[0]  # we get an array atm, so just use first element
        if not j:
            print "project does not exist"
            return False
        else:
            projectId = j["pk"]
            print "project ID: " + str(projectId)
            self.projectId = projectId
            return True


    def createProjectInCloud(self):
        print "Create project: " + self.config["name"]
        url = self.server + "/api/projects/"
        payload = {
            "name": self.config["name"],
            "comment": "no comment",
        }
        r = requests.post(url, json=payload, auth=self.auth)
        print "Response: " + str(r)


    def uploadData(self, data):
        print "Upload data"
        url = self.server + "/api/crashdata/"

        myMsgList = []
        n = 0
        for msg in data["fuzzIterData"]["fuzzedData"]:
            m = {
                "index": n,
                "sentBy": msg["from"],
                "msg": base64.b64encode( msg["data"] ),
                "fuzzed": 0,
            }
            myMsgList.append(m)
            n += 1

        # convert some ugly data
        registers = ''.join('{}={} '.format(key, val) for key, val in data["verifyCrashData"]["registers"].items())
        backtraceStr = '\n'.join(map(str, data["verifyCrashData"]["backtrace"]))

        # temporary fix
        if "reallydead" not in data["initialCrashData"]:
            data["initialCrashData"]["reallydead"] = 23

        # decide which data has precedence for displaying
        codeaddr = 0
        cause = ""
        cause_line = ""
        backtrace = ""
        if "asanData" in data["verifyCrashData"]:
            asanData = data["verifyCrashData"]["asanData"]

            codeaddr = int(asanData["pc"], 16)
            cause = asanData["cause"]
            cause_line = asanData["cause_line"]
            backtrace = asanData["backtrace"]
        else:
            codeaddr = data["verifyCrashData"]["faultAddress"]
            backtrace = backtraceStr
            cause = "n/a"
            cause_line = "n/a"


        payload = {
            "project": self.projectId,
            "seed": data["fuzzIterData"]["seed"],
            "offset": data["verifyCrashData"]["faultOffset"],
            "module": data["verifyCrashData"]["module"],
            "signal": data["verifyCrashData"]["sig"],
            "time": "2017-09-09T18:03",
            "stdout": data["verifyCrashData"]["stdOutput"],
            "asanoutput": data["verifyCrashData"]["asanOutput"],
            "backtrace": backtrace,

            "fuzzerpos": data["initialCrashData"]["fuzzerPos"],
            "reallydead": data["initialCrashData"]["reallydead"],

            "cause": cause,
            "cause_line": cause_line,

            "codeoff": data["verifyCrashData"]["faultOffset"],
            "codeaddr": codeaddr,
            "stackoff": 5,  # data["verifyCrashData"]["stackAddr"]
            "stackaddr": data["verifyCrashData"]["stackPointer"],

            "registers": registers,
            "messageList": myMsgList,
        }
        #print "JSON: " + json.dumps(payload)
        r = requests.post(url, json=payload, auth=self.auth)
        print "Code: " + str(r.status_code)
        if r.status_code != 200:
            pprint.pprint(payload)
            print "R: " + r.text
