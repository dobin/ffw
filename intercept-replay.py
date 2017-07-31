#!/usr/bin/env python

import pickle 
import sys

if __name__ == '__main__':
	fileName = sys.argv[1]

	with open(fileName,'rb') as f:
		datas = pickle.load(f)

	for data in datas:
		print "From: " + data["from"]
