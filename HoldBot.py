#!/usr/bin/env python3
from BaseClient import BaseClient
from language import *

class HoldBot(BaseClient):
    def __init__(self, host='127.0.0.1', port=16713):
        BaseClient.__init__(self, host, port)
        self.name = 'HoldBot'
        self.version = '1.0'

    def handle_SCO(self, msg):
        pass
        

if __name__ == '__main__':
    bot = HoldBot()
    bot.register()
    while True:
        msg = bot.recv_msg()
        if msg:
            bot.print_incoming_message(msg)
            bot.handle_incoming_message(msg)
