#!/usr/bin/python
#-*- coding=utf-8 -*-

__author__ = ['"wuyadong" <wuyadong@tigerknows.com>']

import socket
from selectpoll import SelectPoll

#TODO 有socket未被正常关闭(非常严重的bug)
if __name__ == "__main__":
    # response
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

    select_poller = SelectPoll()
    # 注册一个server socket
    select_poller.register(server_socket.fileno(), SelectPoll.READ)

    try:
        connections = {}
        requests = {}
        responses = {}

        while True:
            # 等待事件
            events = select_poller.poll(0.01)

            # 处理事件
            for fd, event in events:

                # 有client接入
                if fd == server_socket.fileno():
                    connection, address = server_socket.accept()
                    connection.setblocking(0)
                    select_poller.register(connection.fileno(), SelectPoll.READ)
                    # 记录
                    connections[connection.fileno()] = connection
                    requests[connection.fileno()] = ""
                    responses[connection.fileno()] = response
                    print "one socket connect"

                # 处理client有数据输入的情况
                elif event & SelectPoll.READ:
                    requests[fd] += connections[fd].recv(100)
                    if EOL1 in requests[fd] or EOL2 in requests[fd]:
                        select_poller.modify(fd, SelectPoll.WRITE)
                        print "one socket write"

                # 处理向client输出数据的情况
                elif event & SelectPoll.WRITE:
                    bytes_writtern = connections[fd].send(responses[fd])
                    responses[fd] = responses[fd][bytes_writtern:]
                    if len(responses[fd]) == 0:
                        select_poller.unregister(fd)
                        # connections[fd].close()
                        connections[fd].shutdown(socket.SHUT_RDWR)
                        connections[fd].close()
                        requests.pop(fd, None)
                        responses.pop(fd, None)
                        connections.pop(fd, None)
                        print "remove one socket"

                # 处理错误情况
                elif event & SelectPoll.ERROR:
                    select_poller.unregister(fd)
                    connections[fd].shutdown(socket.SHUT_RDWR)
                    connections[fd].close()
                    requests.pop(fd, None)
                    responses.pop(fd, None)
                    print "error one socket"

    finally:
        select_poller.unregister(server_socket.fileno())
        select_poller.close()
        server_socket.close()