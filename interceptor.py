#!/usr/bin/env python

import socket
import threading
import select
import sys
import pickle 

# based on: https://gist.github.com/sivachandran/1969859

terminateAll = False

class ClientThread(threading.Thread):
	def createDataEntry(self, frm, data):
		data = {
			"from": frm, 
			"data": data,
		}

		return data


	def __init__(self, clientSocket, targetHost, targetPort, threadId):
		threading.Thread.__init__(self)
		self.__clientSocket = clientSocket
		self.__targetHost = targetHost
		self.__targetPort = targetPort
		self.__threadId = threadId
		self.data = []
		

	def run(self):
		print "Client Thread" + self.__threadId + " started"
		
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
		with open("data_" + str(threadId) + ".pickle", 'wb') as f:
			pickle.dump(self.data, f)


if __name__ == '__main__':
	if len(sys.argv) != 5:
		print 'Usage:\n\tpython %s <host> <port> <remote host> <remote port>' % sys.argv[0]
		print 'Example:\n\tpython %s localhost 8080 www.google.com 80' % sys.argv[0]
		sys.exit(0)		
	
	localHost = sys.argv[1]
	localPort = int(sys.argv[2])
	targetHost = sys.argv[3]
	targetPort = int(sys.argv[4])
		
	serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serverSocket.bind((localHost, localPort))
	serverSocket.listen(5)
	print "Waiting for client..."
	threadId = 0
	while True:
		try:
			clientSocket, address = serverSocket.accept()
		except KeyboardInterrupt:
			print "\nTerminating all clients..."
			terminateAll = True
			break

		ClientThread(clientSocket, targetHost, targetPort, threadId).start()
		threadId += 1
		
	serverSocket.close()