#!/usr/bin/env python

import socket
import threading
import select
import sys
import pickle 
import glob 
import os

import ffwchild

"""
	Interceptor.py, standalone binary

	it perform a man-in-the-middle attack
	the client has to connect to the specific port of this tool
	all data will be forwarded to the server, and vice-versa

	interceptor will also record all transmitted data, split up between
	read()'s, and split between server and client

	It will store the data in files with the name data_<connid>.pickle,
	serialized python objects as pickle

	This can be used later to fuzz server (or client) with ffw interceptor mode, 
	which excpects pickle file recorded here. 

	A recorded connection can be replayed to test it. 
"""


# based on: https://gist.github.com/sivachandran/1969859 (no license)

terminateAll = False

class ClientThread(threading.Thread):
	def createDataEntry(self, frm, data):
		data = {
			"from": frm, 
			"data": data,
		}

		return data


	def __init__(self, config, clientSocket, targetHost, targetPort, threadId):
		threading.Thread.__init__(self)
                self.config = config
		self.__clientSocket = clientSocket
		self.__targetHost = targetHost
		self.__targetPort = targetPort
		self.__threadId = threadId
		self.data = []
		

	def run(self):
		print "Client Thread" + str(self.__threadId) + " started"
		
		self.__clientSocket.setblocking(0)
		
		targetHostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		targetHostSocket.connect((self.__targetHost, self.__targetPort))
		targetHostSocket.setblocking(0)
		
		clientData = ""
		targetHostData = ""
		terminate = False
		n = 0
		while not terminate and not terminateAll:
			inputs = [self.__clientSocket, targetHostSocket]
			outputs = []
			
			if len(clientData) > 0:
				outputs.append(self.__clientSocket)
				
			if len(targetHostData) > 0:
				outputs.append(targetHostSocket)
			
			try:
				inputsReady, outputsReady, errorsReady = select.select(inputs, outputs, [], 1.0)
			except Exception, e:
				print e
				break
				
			for inp in inputsReady:
				if inp == self.__clientSocket:
					try:
						data = self.__clientSocket.recv(4096)
					except Exception, e:
						print e
					
					if data != None:
						if len(data) > 0:
							print "Received from client: " + str(self.__threadId) + ": " + str(len(data))
							targetHostData += data
							self.data.append( self.createDataEntry("cli", data) )
							n += 1
						else:
							terminate = True
				elif inp == targetHostSocket:
					try:
						data = targetHostSocket.recv(4096)
					except Exception, e:
						print e
						
					if data != None:
						if len(data) > 0:
							print "Received from server: " + str(self.__threadId) + ": " + str(len(data))
							clientData += data
							self.data.append( self.createDataEntry("srv", data) )
							n += 1
						else:
							terminate = True
						
			for out in outputsReady:
				if out == self.__clientSocket and len(clientData) > 0:
					bytesWritten = self.__clientSocket.send(clientData)
					if bytesWritten > 0:
						clientData = clientData[bytesWritten:]
				elif out == targetHostSocket and len(targetHostData) > 0:
					bytesWritten = targetHostSocket.send(targetHostData)
					if bytesWritten > 0:
						targetHostData = targetHostData[bytesWritten:]
		
		self.__clientSocket.close()
		targetHostSocket.close()
		print "ClientThread terminating"

		# store all the stuff
		print "Got " + str(len(self.data)) + " packets"
		fileName = self.config["inputs"] + "/" + "data_" + str(self.__threadId) + ".pickle"
		with open(fileName, 'wb') as f:
			pickle.dump(self.data, f)


def performIntercept(config, localHost, localPort, targetHost, targetPort):
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverSocket.bind((localHost, int(localPort)))
	serverSocket.listen(5)
	print "Forwarding everything to %s:%s" % (targetHost, targetPort)
	print "Waiting for client on port: " + str(localPort)
	threadId = 0
	while True:
		try:
			clientSocket, address = serverSocket.accept()
		except KeyboardInterrupt:
			print "\nTerminating all clients..."
			terminateAll = True
			break

		ClientThread(config, clientSocket, targetHost, targetPort, threadId).start()
		threadId += 1
		
	serverSocket.close()


# called from ffw
def doIntercept(config, localPort):
	localHost = "localhost"
	targetHost = "localhost"

	targetPort = int(localPort) + 1
	config["target_port"] = targetPort

	# run the server, as configured in config
	ffwchild._runTarget(config)

	# start mitm server
	performIntercept(config, localHost, localPort, targetHost, targetPort)


def replayAll(config):
	print "Replay all files from " + config["inputs"]

	config["target_port"] = config["baseport"]

	# find files
	files = sorted(glob.glob(os.path.join(config["inputs"], '*.pickle')), key=os.path.getctime)
	print "Replay %i files" % len(files)

	# start server
	ffwchild._runTarget(config)

	for file in files:
		replayIntercept(config, file)


def replayIntercept(config, fileName):
	print "Replay: " + fileName
	with open(fileName,'rb') as f:
		datas = pickle.load(f)
		f.close()

	targetHostSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	targetHostSocket.connect(("localhost", config["target_port"]))

	for data in datas:
		if data["from"] == "cli":
			print "  Send: " + str(len(data["data"]))
			targetHostSocket.send(data["data"])
		else:
			print "  Receive"
			print "    expect: " + str(len(data["data"]))
			d = targetHostSocket.recv(2048)
			print "    Got:    " + str(len(d))

	targetHostSocket.close()


# manual start
if __name__ == '__main__':
	if len(sys.argv) != 5:
		print 'Usage:\n\tpython %s <host> <port> <remote host> <remote port>' % sys.argv[0]
		print 'Example:\n\tpython %s localhost 8080 www.google.com 80' % sys.argv[0]
		sys.exit(0)		
	
	localHost = sys.argv[1]
	localPort = int(sys.argv[2])
	targetHost = sys.argv[3]
	targetPort = int(sys.argv[4])

	performIntercept(localHost, localPort, targetHost, targetPort)

