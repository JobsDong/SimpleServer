#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import time
import socket
from errno import  EWOULDBLOCK, ECONNRESET, \
	ENOTCONN, ESHUTDOWN, ECONNABORTED
import logging

from util import except_info


class ClientException(Exception):
	"""client error
	"""


class CloseClientException(Exception):
	"""fake exception, close
	"""


class Client(object):

	READ_BUFFER_SIZE = (1 << 12)  # 4kb
	MAX_READ_BUFFER_SIZE = (1 << 16)  # 16kb
	WRITE_BUFFER_SIZE = (1 << 18)  # 256kb
	IDLE_TIMEOUT = 60 * 5  # 5 minutes

	def __init__(self, socket):
		self.socket = socket
		self.address = socket.getpeername()
		self.read_buffer = ""
		self.write_buffer = ""
		self.running = True
		self.last_activity = time.time()

		self.init()

		self.logger = logging.getLogger()
		self.logger.info("%s:%s - Connection" % (self.address[0], self.address[1]))

	def read(self):
		"""

		:return:
		"""
		if self.running and (self.socket is not None):
			try:
				data = self.socket.recv(self.READ_BUFFER_SIZE)
				if not data:
					self.running = False
					self.socket.shutdown(socket.SHUT_RDWR)
					raise CloseClientException("read, but empty data")

			except socket.error, e:
				if e.args[0] in (ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED):
					self.running = False
					self.socket.shutdown(socket.SHUT_RDWR)
					raise ClientException("socket read error:%s" % except_info())
				else:
					raise
			self.read_buffer += data
			if len(self.read_buffer) > self.MAX_READ_BUFFER_SIZE:
				raise ClientException("Maxread buffer size reached")

	def write(self):
		"""

		:return:
		"""
		if self.running and (self.socket is not None) and (len(self.write_buffer) > 0):
			try:
				result = self.socket.send(self.write_buffer)
			except socket.error, e:
				if e.args[0] == EWOULDBLOCK:
					return
				elif e.args[0] in (ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED):
					self.running = False
					self.socket.shutdown(socket.SHUT_RDWR)
				else:
					raise
			else:
				print result, self.write_buffer
				self.write_buffer = self.write_buffer[result:]
				self.last_activity = time.time()

	def close(self):
		try:
			self.socket.close()
		except:
			pass
		self.socket = None
		self.read_buffer = ""
		self.write_buffer = ""
		self.running = False

	def process(self):
		if not self.running:
			return
		if (time.time() - self.last_activity) > Client.IDLE_TIMEOUT:
			return
		if len(self.read_buffer) > 0:
			pos = 0
			length = len(self.read_buffer)
			while length > 0:
				message = self.readMessage(buffer(self.read_buffer, pos))
				if message is None:
					break
				else:
					pos += message[0]
					length -= message[0]
					if message[1] is not None:
						self.processMessage(message[1])
			if pos > 0:
				self.read_buffer = self.read_buffer[pos:]
			self.last_activity = time.time()

	def writeMessage(self, data):
		if data is not None:
			self.write_buffer += data

	def readMessage(self, message):
		"""read message

		:param message:
		:return:
		"""
		raise NotImplementedError

	def processMessage(self, message):
		"""process message

		:param message:
		:return:
		"""
		raise NotImplementedError

	def init(self):
		"""init

		:return:
		"""
		raise NotImplementedError