#!/usr/bin/python
# -*- coding=utf-8 -*-


__author__ = ['"wuyadong" <wuyadong311521@gmail.com>']

from client import Client


class HttpClient(Client):

	response = "HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n"
	response += "Content-Type: text/plain\r\nContent-Length: 11\r\n\r\n"
	response += "Hello World"

	def init(self):
		pass

	def readMessage(self, message):
		message = str(message)
		print message
		return len(message), "WRITE"

	def processMessage(self, message):
		self.writeMessage(HttpClient.response)


if __name__ == "__main__":
	from server import Server
	http_server = Server(CLIENT_CLASS=HttpClient)
	http_server.start(("127.0.0.1", 8080))