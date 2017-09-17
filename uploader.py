#!/usr/bin/env python2

import os
import glob
import requests
import json
import base64

import utils

class Uploader(object):
    def __init__(self, config):
        self.config = config
        self.server = "http://localhost:8000"
        self.projectId = None

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


    def projectExistsInCloud(self):
        payload = {'name': self.config["name"]}
        url = self.server + "/api/projects/"
        r = requests.get(url, params=payload)

        j = r.json()
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
        r = requests.post(url, json=payload)
        print "Response: " + str(r)


    def uploadData(self, data):
        print "Upload data"
        url = self.server + "/api/crashdata/"

        myMsgList = []
        for msg in data["fuzzIterData"]["fuzzedData"]:
            m = {
                "index": 0,
                "sentBy": msg["from"],
                "msg": base64.b64encode( msg["data"] ),
                "fuzzed": 0,
            }
            myMsgList.append(m)

        payload = {
            "project": self.projectId,
            "seed": data["fuzzIterData"]["seed"],
            "offset": data["verifyCrashData"]["faultOffset"],
            "module": data["verifyCrashData"]["module"],
            "signal": data["verifyCrashData"]["sig"],
            "time": "2017-09-09T18:03",
            "stdout": data["verifyCrashData"]["stdOutput"],
            "asanoutput": data["verifyCrashData"]["asanOutput"],
            "filename": "fuck",
            "messageList": myMsgList,
        }
        r = requests.post(url, json=payload)
        print r.text
