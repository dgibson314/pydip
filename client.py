#!/usr/bin/env python3
import struct
import socket

from language import Message, Token
from tokens import *

class BaseClient():
    def __init__(self, host='127.0.0.1', port=16713):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        self.name = 'BaseClient'
        self.version = 1

    def connect(self):
        '''
        Opens a socket connection to the DAIDE server
        '''
        server_address = (self.host, self.port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(server_address)
            self.connected = True
        except:
            print("Unable to connect.\n")

    def close(self):
        '''
        Closes socket connection to the DAIDE server
        '''
        self.sock.close()
        self.connected = False

    def get_header(self):
        if (self.connected):
            header = self.sock.recv(4)
            (msg_type, pad, msg_len) = struct.unpack('!hhl', header)
            return (msg_type, msg_len)
        else:
            raise Exception("Not connected to server.")

    def recv_msg(self):
        try:
            (msg_type, msg_len) = self.get_header()

            bufsize = 1024
            bytes_recvd = 0
            msg = []
            while (bytes_recvd < msg_len):
                chunk = self.sock.recv(min(msg_len - bytes_recvd, bufsize))
                if chunk == b'':
                    raise RuntimeError("socket connection broken")
                msg.append(chunk)
                bytes_recvd = bytes_recvd + len(chunk)
            return b''.join(msg)
        except Exception as e:
            print(e)

    def write(self, message, msg_type):
        byte_length = len(message)
        header = struct.pack('!bxh', msg_type, byte_length)

        print("HEADER: \t", header)
        print("MESSAGE: \t", message)

        message = header + message
        print(len(message))
        self.sock.send(message)

    def send_obs(self):
        msg = Message(OBS).pack()
        self.write(msg, 2)

    def send_nme(self):
        pass

    def send_iam(self):
        pass

    def send_initial_msg(self):
        msg = struct.pack('!HH', self.version, 0xDA10)
        self.write(msg, 0)

b = BaseClient()
b.connect()
b.send_initial_msg()
b.send_obs()
while True:
    b.sock.recv(1024)
