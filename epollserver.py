#!/usr/bin/python
#-*- coding=utf-8 -*-

"""用select模块中epoll接口(水平触发)，写一个简易的http server
"""

__author__ = ['"wuyadong" <wuyadong@tigerknows.com>']

import select
import socket

#TODO socket未正常关闭的bug
if __name__ == "__main__":
    # response
    EOL1 = "\n\n"
    EOL2 = "\n\r\n"
    response = "HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n"
    response += "Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n"
    response += "Hello World"

    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setblocking(0)
    server_socket.bind(("0.0.0.0", 8080))
    server_socket.listen(25)

    poller = select.epoll(1)
    poller.register(server_socket.fileno(), select.EPOLLIN)

    connections = {}
    requests = {}
    responses = {}

    try:
        while True:
            events = poller.poll(1)
            print events

            for fd, event in events:
                # 有client接入服务器
                if fd == server_socket.fileno():
                    connection, address = server_socket.accept()
                    connection.setblocking(0)
                    connections[connection.fileno()] = connection
                    requests[connection.fileno()] = ""
                    responses[connection.fileno()] = response
                    poller.register(connection.fileno(), select.EPOLLIN)
                    print "one socket connect"

                elif event & select.EPOLLIN:
                    requests[fd] += connections[fd].recv(100)

                    if EOL1 in requests[fd] or EOL2 in requests[fd]:
                        poller.modify(fd, select.EPOLLOUT)
                        print "one socket write"

                elif event & select.EPOLLOUT:
                    bytes_writtern = connections[fd].send(responses[fd])
                    responses[fd] = responses[fd][bytes_writtern:]

                    if len(responses[fd]) == 0:
                        poller.modify(fd, 0)
                        connections[fd].shutdown(socket.SHUT_RDWR)
                        connections.pop(fd, None)
                        requests.pop(fd, None)
                        responses.pop(fd, None)
                        print "one socket remove"

                elif event & select.EPOLLHUP:
                    poller.unregister(fd)
                    connections[fd].close()
                    connections.pop(fd, None)
                    requests.pop(fd, None)
                    responses.pop(fd, None)
                    print "one socket error"

    finally:
        poller.unregister(server_socket.fileno())
        poller.close()
        server_socket.close()



