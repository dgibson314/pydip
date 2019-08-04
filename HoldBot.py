#!/usr/bin/env python3
from BaseClient import BaseClient
from language import *
from gameboard import *


class HoldBot(BaseClient):
    '''
    A quite simple bot that issues hold orders to all
    of its units. Any (unlikely) builds are waived, and
    all dislodged units are disbanded.
    '''
    def __init__(self, host='127.0.0.1', port=16713):
        BaseClient.__init__(self, host, port)
        self.name = 'HoldBot'
        self.version = '1.0'

    def generate_orders(self):
        units = self.map.get_own_units()
        print(units)
        # Movement phase
        if self.map.season in [SPR, FAL]:
            for unit in units:
                self.map.add(HoldOrder(unit))
        # Retreat phase
        elif self.map.season in [SUM, AUT]:
            for unit, _ in self.map.retreat_opts.items():
                self.map.add(DisbandOrder(unit))
        # Adjustment phase
        else:
            build_num = self.map.build_number()
            # More units than sc's; need to remove some units
            if build_num < 0:
                unordered = self.map.get_unordered()
                for i in range(abs(build_num)):
                    self.map.add(RemoveOrder(unordered[i]))
            # Somehow got more sc's; need to waive all builds
            elif build_num > 0:
                for i in range(build_num):
                    self.map.add(WaiveOrder(self.power))


if __name__ == '__main__':
    bot = HoldBot()
    bot.register()
    while True:
        msg = bot.recv_msg()
        if msg:
            bot.print_incoming_message(msg)
            bot.handle_incoming_message(msg)
