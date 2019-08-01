from language import *


class Gameboard():
    '''
    Stores info about current turn and current unit positions.

    The following instance variables refer to the initial game state, and will
    remain unchanged throughout the game.
    - powers            List of powers
    - home_centers      Dictionary of powers mapped to their home SCs
    - adjacencies       Mimics the structure of MDF adjacency list, e.g.
                        [[prov_adj][prov_adj]...], where [prov_adj] is of the form
                        [province [unit_type adj_prov adj_prov...]...]...].
                        See the DAIDE Message Syntax section on the MDF message
                        for more details.

    The following instance variables are updated as the game progresses,
    (probably) by being passed NOW and SCO messages from the DAIDE server.
    - supply_centers    Mapping from powers to a list of SCs they have
                        after each Fall Retreat turn
    - units             Mapping from powers to a list of Units, each of
                        the form (power, unit_type, province)
    - year              Current year, e.g. 1901, 1902, etc.
    - season            One of:
                            SPR: Spring moves
                            SUM: Spring retreats
                            FAL: Fall moves
                            AUT: Fall retreats
                            WIN: Adjustments

    The Gameboard also stores the orders, and they can be retrieved in a
    Message format which can then be sent to the DAIDE server. Once the
    server has adjudicated, the results should be passed back to this
    class, which then updates the current positions.
    - orders            Mapping from Units to Orders, Units consisting of
                        the form (power, unit_type, province)
    - retreat_opts      Mapping from Units that must retreat to a list
                        of provinces they're able to retreat to. An
                        empty list signals the unit has no possible
                        retreats.

    '''
    def __init__(self, power, MDF_message):
        self.power_played = power
        self.powers = []
        self.home_centers = {}
        self.adjacencies = {}

        self.supply_centers = {}
        self.units = {}
        self.year = None
        self.season = None

        self.orders = {}
        self.retreat_opts = {}

        folded_msg = MDF_message.fold()

        # Adding powers
        for power in folded_msg[1]:
            self.powers.append(power)
            # Initializing self.units to power<->[]
            self.units[power] = []

        # Adding supply centerstuples
        sc_section = folded_msg[2][0]
        for sc_lst in sc_section:
            power = sc_lst[0]
            self.home_centers[power] = sc_lst[1:]

        # Adding adjacencies
        adjacencies = folded_msg[3]
        for prov_adj in adjacencies:
            province = prov_adj[0]
            self.adjacencies[province] = {}
            adjs = prov_adj[1:]
            for adj in adjs:
                unit_type = adj[0]
                if isinstance(unit_type, list):
                    # unit_type <-> [FLT coast]
                    pass
                else:
                    self.adjacencies[province][unit_type] = adj[1:]

    def update_supply_centers(self, SCO_message):
        '''
        Updates the current supply center ownership by traversing an
        SCO message from the DAIDE server. Unowned centers are listed
        against the power name UNO.
        '''
        folded_SCO = SCO_message.fold()
        for position in folded_SCO[1:]:
            power = position[0]
            centers = position[1:]
            self.supply_centers[power] = []
            for center in centers:
                self.supply_centers[power].append(center)

    def update_turn_and_units(self, NOW_message):
        ''' 
        Updates current turn and unit positions by traversing a
        NOW message from the DAIDE server.
        '''
        folded_NOW = NOW_message.fold()
        self.season = folded_NOW[1][0]
        self.year = folded_NOW[1][1]

        positions = folded_NOW[2:]
        for position in positions:
            power = position[0]

            # clear out old unit positions
            self.units[power] = []

            # add updated unit
            unit_type = position[1]
            province = position[2]
            unit = Unit(power, unit_type, province)
            self.units[power].append(unit)

            # Update MRT retreat options, if necessary
            if MRT in position:
                m_index = postion.index(MRT)
                self.retreat_opts[unit] = position[m_index+1:]

        # Clear out orders
        # TODO: perhaps unneccessary/harmful?
        self.clear_orders()

    def clear_orders(self):
        self.orders = {}
        owned_units = self.get_own_units()
        for unit in owned_units:
            self.orders[unit] = []

    def get_units(self, power):
        return self.units[power]

    def get_own_units(self, power):
        return self.get_units(self.power_played)

    def get_supply_centers(self, power):
        return self.supply_centers[power]

    def get_orders(self):
        '''
        Returns a Message corresponding to a list of orders in DAIDE format,
        i.e. (order) (order) ...
        The client will need to append this Message to a 'SUB' token before
        submitting to the server. Alternatively, the client can append the
        Message to 'SUB (turn)' for additional peace-of-mind.
        See section 3 of the DAIDE syntax document for more details.
        '''
        units = self.get_own_units()
        pass

    def get_orders_message(self):
        pass

    def add_order(self, order):
        ''' 
        Adds Order to the self.orders mapping, removing
        any prior orders that belong to the same unit.
        '''
        # TODO: handle possibility of KeyError?
        unit = order.unit
        self.orders[unit] = order


class Unit():
    # TODO: would it be better for this to be a named-tuple?
    # May want to add 'note' attribute later?
    def __init__(self, power, unit_type, province):
        self.power = power
        self.unit_type = unit_type
        self.province = province

    def __repr__(self):
        return 'Unit(%s, %s, %s)' % (self.power, self.unit_type, self.province)

    def __str__(self):
        result = ''
        result += str(self.power) + ' '
        result += str(self.unit_type) + ' '
        result += str(self.province)
        return result

    def tokenize(self):
        return Message(self.power, self.unit_type, self.province)

    def wrap(self):
        return self.tokenize().wrap()


class HoldOrder():
    def __init__(self, unit):
        self.unit = unit

    def __repr__(self):
        return "HoldOrder(%s)" % (repr(self.unit))

    def __str__(self):
        return "Hold(%s)" % (self.unit)

    def get_message(self):
        return (self.unit.wrap() ++ HLD).wrap()


class MoveOrder():
    def __init__(self, unit, destination):
        self.unit = unit
        self.dest = destination

    def __repr__(self):
        return "MoveOrder(%s, %s)" % (repr(self.unit), self.dest)

    def __str__(self):
        return "Move(%s -> %s)" % (self.unit, self.dest)

    def get_message(self):
        return (self.unit.wrap() ++ MTO ++ self.dest).wrap()


class SupportHoldOrder():
    def __init__(self, unit, supported):
        self.unit = unit
        self.supported = supported

    def __repr__(self):
        return "SupportHoldOrder(%s, %s)" % (repr(self.unit), repr(self.supported))

    def __str__(self):
        return "SupportHold(%s | %s)" % (self.unit, self.supported)

    def get_message(self):
        return (self.unit.wrap() ++ SUP + self.supported.wrap()).wrap()


class SupportMoveOrder():
    def __init__(self, unit, sup_unit, destination):
        self.unit = unit
        self.supported = sup_unit
        self.dest = destination

    def __repr__(self):
        return "SupportMoveOrder(%s, %s, %s)" % (repr(self.unit), repr(self.supported), self.dest)

    def __str__(self):
        return "SupportMove(%s | %s -> %s)" % (self.unit, self.supported, self.dest)


class ConvoyOrder():
    def __init__(self, unit, cvy_unit, destination):
        self.unit = unit
        self.cvy_unit = cvy_unit
        self.dest = destination

    def __repr__(self):
        return "ConvoyOrder(%s, %s)" % (repr(self.unit), repr(self.cvy_unit), self.dest)

    def __str__(self):
        return "Convoy(%s ^ %s -> %s)" % (self.unit, self.cvy_unit, self.dest)


class MoveByConvoyOrder():
    def __init__(self, unit, path):
        self.unit = unit
        self.path = path

    def __repr__(self):
        pass


if __name__ == '__main__':
    unit = Unit(ENG, FLT, LON)
    sup_unit = Unit(ENG, AMY, LVP)
    m = SupportHoldOrder(unit, sup_unit)
    print(m.get_message())
