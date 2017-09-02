#!/bin/python
import pickle
import pprint
import sys

def printpickle():
	pp = pprint.PrettyPrinter(indent=4)

	with open(sys.argv[1],'rb') as f:
		p = pickle.load(f)
		pp.pprint(p)

printpickle()
