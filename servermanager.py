#!/bin/python

import time
import logging
import os
import subprocess
import socket

import network
import serverutils

GLOBAL_SLEEP = {
    # how long to wait after server start
    # can be high as it is not happening so often
    "sleep_after_server_start": 1,
}


class ServerManager(object):
	"""
		Manages all interaction with the server (the fuzzing target)
		This includes:
			- handling the process (start, stop)
			- network communication
	"""

	def __init__(self, config, threadId):
		self.config = config
		self.process = None
		self.sock = None
	 	self.targetPort = self.config["baseport"] + threadId
		serverutils.setupEnvironment(self.config)


	def start(self):
		"""Start the server"""
		self.process = self._runTarget()


	def stop(self):
		"""Stop the server"""
		self.process.terminate


	def restart(self):
		self.stop()
		time.sleep(GLOBAL_SLEEP["sleep_after_server_start"])
		self.start()
		time.sleep(GLOBAL_SLEEP["sleep_after_server_start"])


	def isStarted(self):
		"""Return true if server is started"""


	def isAliveSlow(self):
		"""Return true if the server is alive"""
		return network.testServerConnection(self.targetPort)


    ##################
	def openConnection(self):
		"""
		Opens a TCP connection to the server
		True if successful
		False if not (server down)

		Note: This is also used to test if the server
		has crashed
		"""
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_address = ('localhost', self.targetPort)
		logging.info("Open connection on localhost:" + str(self.targetPort))
		try:
		    self.sock.connect(server_address)
		except socket.error, exc:
			# server down
			logging.info("  Could not connect! Server is down.")
			return False

		return True


	def closeConnection(self):
		socket.close()


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
    ##################

	def _waitForServer(self):
		"""
		Blocks until server is alive
		Used to block until it really started
		"""


	def getCrashData(self):
		"""
		Return the data of the crash
		or None if it has not crashed (should not happen)
		"""
		crashData = {
			"asanOutput": serverutils.getAsanOutput(self.config, self.process.pid),
			"signum": 0,
			"exitcode": 0,
		}

		return crashData


	def _runTarget(self):
		"""
		Start the server
		"""
		global GLOBAL_SLEEP
		popenArg = serverutils.getInvokeTargetArgs(self.config, self.targetPort)
		logging.info("Starting server with args: " + str(popenArg))

		# create devnull so we can us it to surpress output of the server (2.7 specific)
		DEVNULL = open(os.devnull, 'wb')
		p = subprocess.Popen(popenArg, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
		time.sleep( GLOBAL_SLEEP["sleep_after_server_start"] ) # wait a bit so we are sure server is really started
		logging.info("  Pid: " + str(p.pid) )

		return p
