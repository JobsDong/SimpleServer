#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import logging
import socket

from poll import SelectPoll, Poll
from handler import Handler
import util


class Server(object):

	def __init__(self, POLL_CLASS=SelectPoll, LISTEN_COUNT=10,
	             MAX_HANDLERS=10, MAX_CLIENTS=100):
		# settings
		self.POLL_CLASS = POLL_CLASS
		self.LISTEN_COUNT = LISTEN_COUNT
		self.MAX_HANDLERS = MAX_HANDLERS
		self.MAX_CLIENTS = MAX_CLIENTS

		self.server_sock = None
		self.poll = self.POLL_CLASS()
		self.handlers = []
		self.logger = logging.getLogger()

	def start(self, address):
		try:
			# server socket
			self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server_sock.setbloking(0)
			self.server_sock.bind(address)
			self.server_sock.listen(self.LISTEN_COUNT)
			self.poll.register(self.server_sock.fileno(), Poll.READ | Poll.ERROR)

			# handlers
			self.handlers = [Handler(self) for i in xrange(self.MAX_HANDLERS)]

			# loop
			self.loop()
		except:
			self.logger.error(util.except_info())

		# close socket
		try:
			self.poll.unregister(self.server_sock.fileno())
			self.server_sock.close()
		except:
			# ignore
			pass
		self.server_sock = None

	def loop(self):
		"""dispatch socket to handler

		:return:
		"""
		while True:
			try:
				events = self.poll.poll(0.01)

				for fd, event in events:
					# connect
					if fd == self.server_sock.fileno():
						if event & Poll.ERROR:
							break
						elif event & Poll.READ:
							self._connect()
			except:
				self.logger.error(util.except_info())
				break

	def _connect(self):
		connection, address = self.server_sock.accept()
		connection.setblocking(0)

		# min clients handler
		client_count, handler = min([(len(handler.clients), handler)
		                             for handler in self.handlers])
		if client_count < self.MAX_CLIENTS:
			self.logger.info("PEER [%s:%d] assigned to thread '%s'" %
			                 (address[0], address[1], handler.thread.getName()))
			handler.connect(connection)
		else:
			try:
				connection.close()
			except:
				# ignore
				pass