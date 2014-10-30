#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

import socket

from poll import SelectPoll, Poll
from client import CloseClientException
from http import HttpClient
from util import except_info, console_logger


class Server(object):

	def __init__(self, POLL_CLASS=SelectPoll, CLIENT_CLASS=HttpClient,
	             logger=console_logger, LISTEN_COUNT=10, MAX_CLIENTS=100):
		# settings
		self.POLL_CLASS = POLL_CLASS
		self.CLIENT_CLASS = CLIENT_CLASS
		self.LISTEN_COUNT = LISTEN_COUNT
		self.MAX_CLIENTS = MAX_CLIENTS

		self.server_sock = None
		self.poll = self.POLL_CLASS()
		self.logger = logger
		self.clients = {}
		self.logger.info("init server\nPOLL_CLASS:%s\nCLIENT_CLASS:%s\n"
                 "LISTEN_COUNT:%s\nMAX_CLIENT:%s\n"
                 % (POLL_CLASS, CLIENT_CLASS, LISTEN_COUNT, MAX_CLIENTS))

	def start(self, address):
		try:
			# server socket
			self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server_sock.setblocking(0)
			self.server_sock.bind(address)
			self.server_sock.listen(self.LISTEN_COUNT)
			self.poll.register(self.server_sock.fileno(), Poll.READ | Poll.ERROR)

			self.logger.debug("info:\nserver_sock:%d" % (self.server_sock.fileno()))

			# loop
			self.loop()
		except:
			self.logger.error(except_info())

		# close socket
		self._clean()
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
							self.logger.debug("fd:%d event:ERROR" % fd)
							self.logger.error("server socket error")
							break
						elif event & Poll.READ:
							self.logger.debug("fd:%d event:READ" % fd)
							self._connect()
					elif event & Poll.READ:
						self.logger.debug("fd:%d event:READ" % fd)
						self._read(fd)
					elif event & Poll.WRITE:
						self.logger.debug("fd:%d event:WRITE" % fd)
						self._write(fd)
					elif event & Poll.ERROR:
						self.logger.debug("fd:%d event:ERROR" % fd)
						if fd in self.clients:
							self.clients[fd].close()
							del self.clients[fd]
					self._update(fd)
			except:
				self.logger.error(except_info())
				break

	def _connect(self):
		"""build client, and register

		:return:
		"""
		connection, address = self.server_sock.accept()
		connection.setblocking(0)
		self.logger.debug("client sock:%d" % connection.fileno())
		self.logger.info("Peer [%s:%s] connected" % (address[0], address[1]))
		self.clients[connection.fileno()] = self.CLIENT_CLASS(connection)
		self.poll.register(connection.fileno(), Poll.READ | Poll.WRITE | Poll.ERROR)

	def _read(self, fd):
		"""

		:param fd:
		:return:
		"""
		client = self.clients.get(fd, None)
		if client is not None:
			try:
				client.read()
			except CloseClientException:
				self.poll.unregister(fd)
				self.clients[fd]
				client.close()
			except:
				self.logger.warn("one client read error: %s" % except_info())
				self.poll.unregister(fd)
				del self.clients[fd]
				client.close()

		elif fd in self.clients:
			del self.clients[fd]

	def _write(self, fd):
		"""write

		:param fd:
		:return:
		"""
		client = self.clients.get(fd, None)
		if client is not None:
			try:
				client.write()
			except:
				self.logger.warn("one client write error: %s" % except_info())
				self.poll.unregister(fd)
				del self.clients[fd]
				client.close()
		elif fd in self.clients:
			del self.clients[fd]

	def _update(self, fd):
		client = self.clients.get(fd, None)
		if client is not None:
			try:
				client.process()
			except:
				self.logger.warn("one client update error: %s" % except_info())
				self.poll.unregister(fd)
				del self.clients[fd]
				client.close()
		elif fd in self.clients:
			del self.clients[fd]

	def _clean(self):
		for fd, client in self.clients.items():
			self.poll.unregister(fd)
			try:
				client.close()
			except:
				pass
			del self.clients[fd]
