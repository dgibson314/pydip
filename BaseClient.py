#!/usr/bin/env python3
import struct
import socket
import threading

import init
from language import *

class BaseClient():
    def __init__(self, host='127.0.0.1', port=16713):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        self.name = 'BaseClient'
        self.version = '1.0'
        self.power = None
        self.passcode = None
        self.variant = None
        self.press = 0

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
        '''
        Attempts to receive the header of a Diplomacy message
        from the server. Returns a tuple of the message type and
        message length.
        '''
        if (self.connected):
            header = self.sock.recv(4)
            (msg_type, msg_len) = struct.unpack('!bxh', header)
            return (msg_type, msg_len)
        else:
            raise Exception("Not connected to server.")

    def recv_msg(self):
        '''
        Attempts to receive a Diplomacy message from the server.
        Returns a tuple of the message type, message length,
        and actual message.
        '''
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

            if msg:
                return (msg_type, msg_len,  b''.join(msg))

        except Exception as e:
            print(e)

    def write(self, message, msg_type):
        byte_length = len(message)
        header = struct.pack('!bxh', msg_type, byte_length)
        message = header + message
        self.sock.send(message)

    def send_dcsp(self, msg):
        self.write(msg.pack(), 2)

    def send_OBS(self):
        self.send_dcsp(Message(OBS))

    def send_NME(self):
        self.send_dcsp(NME(self.name)(self.version))

    def send_IAM(self):
        # TODO: maybe should check power/passcode != None
        self.send_dcsp(IAM(self.power)(self.passcode))

    def send_initial_msg(self):
        msg = struct.pack('!HH', 1, 0xDA10)
        self.write(msg, 0)

    def request_MAP(self):
        self.send_dcsp(Message(MAP))

    def reply_YES(self, msg):
        self.send_dcsp(YES(msg))

    def reply_REJ(self, msg):
        self.send_dcsp(REJ(msg))

    def process_incoming_message(self, msg):
        msg_type, msg_len, message = msg
        
        if (msg_type == init.RM):
            self.process_representation_message(message)
        elif (msg_type == init.DM):
            self.process_diplomacy_message(message)
        elif (msg_type == init.EM):
            self.process_error_message(message)

    def print_incoming_message(self, msg):
        msg_type, msg_len, message = msg
        message = Message.translate_from_bytes(message)
        message.pretty_print()
        
    def process_diplomacy_message(self, msg):
        msg = Message.translate_from_bytes(msg)
        method_name = 'handle_' + str(msg[0])
        if msg[0] in (YES, REJ):
            method_name += '_' + str(msg[2])
        method = getattr(self, method_name, None)
        if method:
            return method(msg)

    def handle_MAP(self, msg):
        map_name = msg.fold()[1][0]
        if (map_name == 'STANDARD'):
            self.reply_YES(msg)
            self.variant = 'STANDARD'

    def handle_HLO(self, msg):
        self.power = msg.fold()[1][0]
        self.passcode = msg.fold()[1][1]
        self.press = msg.fold()[1][2][1]


if __name__ == '__main__':
    b = BaseClient()
    b.connect()
    b.send_initial_msg()
    b.send_NME()
    while True:
        msg = b.recv_msg()
        if msg:
            b.print_incoming_message(msg)
            b.process_incoming_message(msg)
