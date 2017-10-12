#!/usr/bin/env python2

import pickle
import pprint
import sys

#from verifier import verifierresult


def printpickle():
	pp = pprint.PrettyPrinter(indent=4)

	with open(sys.argv[1], 'rb') as f:
		p = pickle.load(f)
		pp.pprint(p)

if __name__ == '__main__':
	printpickle()
