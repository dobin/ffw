#!/usr/bin/env python

import os


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
    if 'temp' in config:
        if not os.path.exists(config["temp"]):
            os.makedirs(config["temp"])
        else:
            _delDir(config["temp"])

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

    if 'inputs' in config:
        if not os.path.exists(config["input_dir"]):
            os.makedirs(config["input_dir"])
        else:
            _delDir(config["input_dir"])
