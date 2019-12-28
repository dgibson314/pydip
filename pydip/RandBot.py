import random

from BaseClient import BaseClient
from language import *
from gameboard import *


class RandBot(BaseClient):
    '''
    The next step up from the HoldBot.
    TODO: doesn't do Convoying yet.
    '''
    movement_phase_orders = [HoldOrder, MoveOrder]

    def __init__(self, host='127.0.0.1', port=16713):
        BaseClient.__init__(self, host, port)
        self.name = 'HoldBot'
        self.version = '1.0'

    def generate_orders(self):
        units = self.map.get_own_units()
        season = self.map.season

        # Movement phase
        if season in [SPR, FAL]:
            self.generate_movement_orders()
        # Retreat phase
        elif season in [SUM, AUT]:
            self.generate_retreat_orders()
        # Adjustment phase
        else:
            self.generate_adjustment_orders()

    def generate_movement_orders(self):
        for unit in self.map.get_own_units():
            order = random.choice(self.movement_phase_orders)
            if order == MoveOrder:
                adj_provs = self.map.get_adjacencies(unit)
                destination = random.choice(adj_provs)
                self.map.add(order(unit, destination))
            else:
                self.map.add(order(unit))

    def generate_retreat_orders(self):
        for unit, opts in self.map.get_dislodged():
            # No retreat options; disband unit.
            if opts == []:
                self.map.add(DisbandOrder(unit))
            # There is at least one province to retreat to.
            # Choose a random one.
            else:
                retreat_dest = random.choice(opts)
                self.map.add(RetreatOrder(unit, retreat_dest))

    def generate_adjustment_orders(self):
        units = self.map.get_own_units()
        surplus = self.map.sc_surplus()

        # More units than supply centers; randomly remove units
        if surplus < 0:
            random.shuffle(units)
            for i in range(abs(surplus)):
                self.map.add(RemoveOrder(units[i]))

        elif surplus > 0:
            builds, waives = self.map.build_numbers()
            homes = self.map.open_home_centers()
            random.shuffle(homes)
            for i in range(builds):
                province = homes[i]
                coast = None
                if province.is_coastal():
                    unit_type = random.choice([AMY, FLT])
                    if unit_type == FLT and province.is_bicoastal():
                        coast = random.choice(self.map.coasts[province])
                else:
                    unit_type = AMY
                unit = Unit(self.power, unit_type, (province, coast))
                self.map.add(BuildOrder(unit))

            for i in range(waives):
                self.map.add(WaiveOrder(self.power))


if __name__ == '__main__':
    bot = RandBot()
    bot.play()
