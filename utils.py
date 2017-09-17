#!/bin/python
import pickle


def readPickleFile(fileName):
    data = None

    with open(fileName, 'rb') as f:
        data = pickle.load(f)

    return data
