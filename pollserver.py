#!/usr/bin/python
#-*- coding=utf-8 -*-

__author__ = ['"wuyadong" <wuyadong@tigerknows.com>']

import select
import socket

#TODO socket未被关闭的严重bug
if __name__ == "__main__":
    # 设置response
    EOL1 = "\n\n"
    EOL2 = "\n\r\n"
    response = "HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n"
    response += "Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n"
    response += "Hello World"

    # 设置server socket
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setblocking(0)
    server_socket.bind(("0.0.0.0", 8080))
    server_socket.listen(25)

    poller = select.poll()
    poller.register(server_socket, select.POLLIN)

    try:
        connections = {}
        requests = {}
        responses = {}

        while True:
            events = poller.poll(0.01)

            for fd, event in events:
                if fd == server_socket.fileno():
                    connection, address = server_socket.accept()
                    poller.register(connection, select.POLLIN)
                    connections[connection.fileno()] = connection
                    requests[connection.fileno()] = ""
                    responses[connection.fileno()] = response
                    print "one socket connect"

                elif event & select.POLLIN:
                    requests[fd] += connections[fd].recv(100)
                    if EOL1 in requests[fd] or EOL2 in requests[fd]:
                        poller.modify(fd, select.POLLOUT)
                        print "one socket write"

                elif event & select.POLLOUT:
                    bytes_writtern = connections[fd].send(responses[fd])
                    responses[fd] = responses[fd][bytes_writtern:]
                    if len(responses[fd]) == 0:
                        poller.unregister(fd)
                        connections[fd].shutdown(socket.SHUT_RDWR)
                        connections[fd].close()
                        requests.pop(fd, None)
                        responses.pop(fd, None)
                        connections.pop(fd, None)
                        print "remove one socket "

                elif event & select.POLLHUP:
                    poller.unregister(fd)
                    connections[fd].close()
                    requests.pop(fd, None)
                    responses.pop(fd, None)
                    connections.pop(fd, None)
                    print "error one socket"

    finally:
        poller.unregister(server_socket.fileno())
        server_socket.close()