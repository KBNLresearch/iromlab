#!/usr/bin/env python3
"""
Simple socket communication server
Adapted from https://medium.com/python-pandemonium/python-socket-communication-e10b39225a4c
Original code by Rodgers Ouma Mc'Alila
""" 

import sys
import socket
import selectors
import traceback
import queue

class server():

    def start(self, host, port, messageQueue):
        """Start server"""
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the port
        server_address = (host, int(port))
        print('Starting up on {} port {}'.format(*server_address))
        sock.bind(server_address)

        # Listen for incoming connections
        sock.listen(1)

        while True:
            # Wait for a connection
            print('waiting for a connection')
            connection, client_address = sock.accept()
            try:
                print('connection from', client_address)
                myBytes = b''
                # Receive the data in small chunks and retransmit it
                while True:
                    data = connection.recv(16)
                    myBytes += data
                    if data:
                        # print('sending data back to the client')
                        connection.sendall(data)
                    else:
                        # print('no data from', client_address)
                        break
            finally:
                # Decode data to string, and submit it to the queue
                myString = myBytes.decode('utf-8')
                messageQueue.put(myString)
                print("Closing current connection")
                connection.close()

def main():
    host = '127.0.0.1'
    port = 65432
    myServer = server()
    myServer.start(host, port, queue)

if __name__ == "__main__":
    main()