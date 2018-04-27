#!/usr/bin/env python

import os
from configmanager import ConfigManager

from common.networkdata import NetworkData
from common.corpusdata import CorpusData
from common.crashdata import CrashData
from common.verifydata import VerifyData


def _delDir(directory):
    for the_file in os.listdir(directory):
        file_path = os.path.join(directory, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)


def prepareFs(config):
    if 'temp_dir' in config:
        if not os.path.exists(config["temp_dir"]):
            os.makedirs(config["temp_dir"])
        else:
            _delDir(config["temp_dir"])

    if 'outcome_dir' in config:
        if not os.path.exists(config["outcome_dir"]):
            os.makedirs(config["outcome_dir"])
        else:
            _delDir(config['outcome_dir'])

    if 'verified_dir' in config:
        if not os.path.exists(config["verified_dir"]):
            os.makedirs(config["verified_dir"])
        else:
            _delDir(config['verified_dir'])

    if 'input_dir' in config:
        if not os.path.exists(config["input_dir"]):
            os.makedirs(config["input_dir"])
        else:
            _delDir(config["input_dir"])


def getConfig():
    config = {
        "input_dir": "/tmp/ffw-test/corpus",
        "temp_dir": "/tmp/ffw-test/temp",
    }
    basedir = os.path.dirname(os.path.realpath(__file__)) + "/..",

    config['basedir'] = basedir[0]

    return config


def getNetworkData(config):
    networkMessages = [
        {
            'data': 'msg 1 cli',
            'from': 'cli',
            'index': 0,
        },
        {
            'data': 'msg 2 srv',
            'from': 'srv',
            'index': 1,
        }
    ]

    networkData = NetworkData(config,
                              networkMessages)
    return networkData


def getCorpusData(config, networkData=None, filename='data0'):
    if networkData is None:
        networkData = getNetworkData(config)

    corpusData = CorpusData(config, filename, networkData)
    return corpusData


def getCrashData(config):
    corpusData = getCorpusData(config)
    crashData = CrashData(config, corpusData, '-')
    crashData.setCrashInformation(asanOutput="meh")
    return crashData


def getVerifyData(config):
    crashData = getCrashData(config)
    verifyData = VerifyData(config, crashData, faultaddress=1337)
    return verifyData
