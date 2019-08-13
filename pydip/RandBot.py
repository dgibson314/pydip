import random

from BaseClient import BaseClient
from language import *
from gameboard import *


class RandBot(BaseClient):
    '''
    The next step up from the HoldBot.
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
            for unit in units:
                order = random.choice(self.movement_phase_orders)
                if order == MoveOrder:
                    adj_provs = self.map.get_adjacencies(unit)
                    destination = random.choice(adj_provs)
                    self.map.add(order(unit, destination))
                else:
                    self.map.add(order(unit))

        # Retreat phase
        elif season in [SUM, AUT]:
            for unit, opts in self.map.get_dislodged():
                # No retreat options; disband unit.
                if opts == []:
                    self.map.add(DisbandOrder(unit))
                # There is at least one province to retreat to.
                # Choose a random one.
                else:
                    retreat_dest = random.choice(opts)
                    self.map.add(RetreatOrder(unit, retreat_dest))

        # Adjustment phase
        else:
            build_num = self.map.build_number()
            # Select random unit to remove
            if build_num < 0:
                random.shuffle(units)
                for i in range(abs(build_num)):
                    self.map.add(RemoveOrder(units[i]))
            elif build_num > 0:
                home = self.map.open_home_centers()
                random.shuffle(home)
                max_build = min(build_num, len(home))
                delta = build_num - max_build

                for i in range(max_build):
                    province = home[i]
                    coast = None
                    if province.is_coastal():
                        unit_type = random.choice([AMY, FLT])
                        if unit_type == FLT and province.is_bicoastal():
                            coast = random.choice(self.map.coasts[province])
                    else:
                        unit_type = AMY
                    unit = Unit(self.power, unit_type, (province, coast))
                    self.map.add(BuildOrder(unit))

                if delta > 0:
                    for i in range(delta):
                        self.map.add(WaiveOrder(self.power))


if __name__ == '__main__':
    bot = RandBot()
    bot.play()
