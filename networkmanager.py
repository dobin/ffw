#!/bin/python

import socket
import logging
import time

class NetworkManager(object):
	"""
		Opens a network connection to the server
	"""
	def __init__(self, config, targetPort):
		self.config = config
		self.sock = None
		self.targetPort = targetPort


	def openConnection(self):
		"""
		Opens a TCP connection to the server
		True if successful
		False if not (server down)

		Note: This is also used to test if the server
		has crashed
		"""
		self.closeConnection()
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_address = ('localhost', self.targetPort)
		logging.info("Open connection on localhost:" + str(self.targetPort))
		try:
			self.sock.connect(server_address)
		except socket.error, exc:
			# server down
			self.sock.close()
			logging.info("  Could not connect! Server is down.")
			return False

		return True


	def closeConnection(self):
		if self.sock is not None:
			self.sock.close()


	def sendData(self, data):
		"""Send data to the server"""
		try:
			logging.debug("  Send data to server. len: " + str(len(data)))
			self.sock.sendall(data)
		except socket.error, exc:
			logging.debug("Send data exception")
			return False

		return True


	def receiveData(self):
		"""Receive data from the server"""
		socket.settimeout(0.1)
		try:
			data = self.sock.recv(1024)
		except Exception,e:
			return False, None

		return True, data


	def sendMessages(self, msgArr):
	    self.openConnection()
	    for message in msgArr:
	        if message["from"] != "cli":
	            continue

	        self.sendData(message["data"])

	    self.closeConnection()


	def waitForServerReadyness(self):
	    while not self.testServerConnection():
	        print "Server not ready, waiting and retrying"
	        time.sleep(0.1) # wait a bit till server is ready


	def testServerConnection(self):
	    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	    server_address = ('localhost', self.targetPort)

	    try:
	        sock.connect(server_address)
	    except socket.error, exc:
	        # server down
	        return False

	    sock.close()

	    return True
