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
            (msg_type, pad, msg_len) = struct.unpack('!hhl')
            return (msg_type, msg_len)
        else:
            raise Exception("Not connected to server.")

    def recv_msg(self):
        try:
            (msg_type, msg_len) = self.get_header()

            bufsize = 1024
            msg = ''
            while (msg_len > 0):
                if (msg_len > bufsize):
                    msg += self.sock.recv(bufsize)
                    msg_len -= bufsize
                else:
                    msg += self.sock.recv(msg_len)
                    msg_len = 0

            return (msg_type, msg)
        except: print("Unable to get message")

    def write(self, message, msg_type):
        byte_length = max(len(message) // 2, 2)
        header = struct.pack('!hhl', msg_type, 0, byte_length)
        message = header + message
        self.sock.send(message)

    def send_obs(self):
        pass
    def send_iam(self):
        pass

    def send_initial_msg(self):
        msg = struct.pack('!ll', self.version, 0xDA10)
        self.write(msg, 0)

