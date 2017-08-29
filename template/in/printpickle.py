#!/bin/python
import pickle 
import pprint 

def printpickle():
	pp = pprint.PrettyPrinter(indent=4)

	with open("./data_0.pickle",'rb') as f:
		p = pickle.load(f)
		pp.pprint(p)

printpickle()
