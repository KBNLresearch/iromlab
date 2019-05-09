#!/usr/bin/env python3

import sys
import socket
import selectors
import traceback
import queue

from . import libserver

class server():

    sel = selectors.DefaultSelector()

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print("accepted connection from", addr)
        conn.setblocking(False)
        message = libserver.Message(self.sel, conn, addr)
        self.sel.register(conn, selectors.EVENT_READ, data=message)

    def start_server(self, host, port, messageQueue):

        # Set up queue
        #q = queue.Queue()

        lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Avoid bind() exception: OSError: [Errno 48] Address already in use
        lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        lsock.bind((host, port))
        lsock.listen()
        #print("listening on", (host, port))
        lsock.setblocking(False)
        self.sel.register(lsock, selectors.EVENT_READ, data=None)

        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        message = key.data
                        try:
                            message.process_events(mask)
                            if mask & selectors.EVENT_READ:
                                #print(message.request)
                                messageQueue.put(message.request)
                        except Exception:
                            print(
                                "main: error: exception for",
                                f"{message.addr}:\n{traceback.format_exc()}",
                            )
                            message.close()
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            self.sel.close()

def main():
    host = '127.0.0.1'
    port = 65432
    myServer = server()
    myServer.start_server(host, port, queue)


if __name__ == "__main__":
    main()
