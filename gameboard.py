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
    - orders            Mapping from turns to a list of Orders, i.e.
                        (SPR 1901): [HoldOrder(Unit(...)), MoveOrder(Unit(...))...]
    - retreat_opts      Mapping from Units that must retreat to a list
                        of provinces they're able to retreat to. An
                        empty list signals the unit has no possible
                        retreats.

    '''
    def __init__(self, power_played, MDF_message):
        self.power_played = power_played
        self.powers = []
        self.home_centers = {}
        self.adjacencies = {}

        self.supply_centers = {}
        self.units = {}
        self.year = None    # int, not Token
        self.season = None
        self.turn = None    # (season, year)

        self.orders = {}
        self.retreat_opts = {}

        folded_msg = MDF_message.fold()

        # Adding powers
        for power in folded_msg[1]:
            self.powers.append(power)
            # Initializing self.units to power<->[]
            self.units[power] = []

        # Adding supply center tuples
        sc_section = folded_msg[2][0]
        for sc_lst in sc_section:
            power = sc_lst[0]
            self.home_centers[power] = sc_lst[1:]

        # Adding adjacencies
        # See MDF section of DAIDE Syntax document
        adjacencies = folded_msg[3]
        for prov_adj in adjacencies:
            province = prov_adj[0]
            self.adjacencies[province] = {}
            adjs = prov_adj[1:]
            for adj in adjs:
                unit_type = tuple(adj[0]) if isinstance(adj[0], list) else adj[0]
                # [province, [province, coast]] -> [province, (province, coast)]
                adj_provs = [tuple(p) if isinstance(p, list) else p
                             for p in adj[1:]]
                self.adjacencies[province][unit_type] = adj_provs

    def current_turn(self):
        '''
        Returns the current turn in Message format
        '''
        return (self.season + Token.integer(self.year)).wrap()

    def process_SCO(self, SCO_message):
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

    def process_NOW(self, NOW_message):
        '''
        Updates current turn and unit positions by traversing a
        NOW message from the DAIDE server.
        Also adds a new entry for orders to be added for the current
        turn.
        '''
        folded_NOW = NOW_message.fold()
        self.season = folded_NOW[1][0]
        self.year = folded_NOW[1][1]
        self.turn = (self.season, self.year)

        # clear out old unit positions
        self.clear_units()

        positions = folded_NOW[2:]
        for position in positions:
            power = position[0]

            # add updated unit
            unit_type = position[1]
            province = position[2]
            unit = Unit(power, unit_type, province)
            self.units[power].append(unit)

            # Update MRT retreat options, if necessary
            if MRT in position:
                m_index = position.index(MRT)
                self.retreat_opts[unit] = position[m_index+1:]

        # Add a new entry for orders to be added
        self.orders[self.turn] = []

    def process_ORD(self, ORD_message):
        '''
        Updates the corresponding Order with the result.
        See section (iv) of the DAIDE Syntax document for more details.
        '''
        folded_ORD = ORD_message.fold()
        turn = tuple(folded_ORD[1])
        ORD_key = tuple(folded_ORD[2])
        result = folded_ORD[3] if len(folded_ORD[3]) == 3 else tuple(folded_ORD[3])
        for order in self.orders[turn]:
            if order.key == ORD_key:
                order.result = result

    def clear_units(self):
        for power in self.powers:
            self.units[power] = []

    def get_units(self, power):
        return self.units[power]

    def get_own_units(self):
        return self.get_units(self.power_played)

    def get_supply_centers(self, power):
        return self.supply_centers[power]

    def get_orders(self):
        '''
        Returns a Message corresponding to a list of orders in DAIDE format,
        i.e. (order) (order) ...
        The client will need to append this Message to a 'SUB' token before
        submitting to the server. Alternatively, the client can append the
        Message to 'SUB (turn)' for additional peace of mind.
        See section (iii) of the DAIDE syntax document for more details.
        '''
        result = Message()
        for order in self.orders[self.turn]:
            result += order.message()
        return result

    def build_number(self):
        '''
        Calculates the difference between the number of supply centers
        held and the number of units currently in play. Used during
        WIN season for adjustements.
        '''
        sc = len(self.get_supply_centers(self.power_played))
        units = len(self.get_own_units())
        return sc - units

    def missing_orders(self):
        units_ordered = [order.unit for order in self.orders[self.turn]]
        for unit in self.get_own_units():
            if unit not in units_ordered:
                return True
        return False

    def add(self, order):
        '''
        Adds Order to the self.orders mapping, removing
        any prior order that command the same unit.
        '''
        for x in self.orders[self.turn]:
            if x.unit == order.unit:
                self.orders[turn].remove(x)
        self.orders[self.turn].append(order)

    def is_ordered(self, unit):
        '''
        Checks if a unit has already had an Order
        attached to it.
        '''
        for order in self.orders[self.turn]:
            if order.unit == unit:
                return True
        return False

    def get_dislodged(self):
        '''
        Returns list of tuples of all owned units that need to
        retreat and their retreat options.
        '''
        dislodged = []
        for unit, opts in self.retreat_opts.items():
            if unit.power == self.power_played:
                dislodged.append((unit, opts))
        return dislodged

    def get_ordered(self):
        '''
        Returns list of units that have been ordered.
        '''
        return [order.unit for order in self.orders[self.turn]]

    def get_unordered(self):
        '''
        Returns list of units that have not yet been ordered.
        '''
        unordered = []
        for unit in self.get_own_units():
            if not self.is_ordered(unit):
                unordered.append(unit)
        return unordered


class Unit():
    def __init__(self, power, unit_type, province):
        self.power = power
        self.unit_type = unit_type
        if isinstance(province, list) or isinstance(province, tuple):
            self.province = province[0]
            self.coast = province[1]
        else:
            self.province = province
            self.coast = None
        if self.coast:
            self.key = (self.power, self.unit_type, (self.province, self.coast))
        else:
            self.key = (self.power, self.unit_type, self.province)

    def __repr__(self):
        return "Unit(%s, %s, %s, coast=%s)" % (self.power, self.unit_type, self.province, self.coast)

    def __str__(self):
        if self.coast:
            return "%s %s ( %s %s )" % (self.power, self.unit_type, self.province, self.coast)
        else:
            return "%s %s %s" % (self.power, self.unit_type, self.province)

    def tokenize(self):
        if self.coast:
            return Message(self.power, self.unit_type)(self.province, self.coast)
        else:
            return Message(self.power, self.unit_type, self.province)

    def wrap(self):
        return self.tokenize().wrap()


class BaseOrder():
    def __init__(self):
        self.result = None
        self.key = None

    def __str__(self):
        raise NotImplementedError

    def __repr__(self):
        raise NotImplementedError

    def __eq__(self, other):
        return self.key == other.key

    def message(self):
        raise NotImplementedError


class HoldOrder(BaseOrder):
    def __init__(self, unit):
        BaseOrder.__init__(self)
        self.unit = unit
        self.key = (unit.key, HLD)

    def __repr__(self):
        return "HoldOrder(%s)" % (repr(self.unit))

    def __str__(self):
        return "Hold(%s)" % (self.unit)

    def message(self):
        return (self.unit.wrap() ++ HLD).wrap()


class MoveOrder():
    def __init__(self, unit, destination):
        BaseOrder.__init__(self)
        self.unit = unit
        self.dest = destination
        self.key = (unit.key, MTO, destination)

    def __repr__(self):
        return "MoveOrder(%s, %s)" % (repr(self.unit), self.dest)

    def __str__(self):
        return "Move(%s -> %s)" % (self.unit, self.dest)

    def message(self):
        return (self.unit.wrap() ++ MTO ++ self.dest).wrap()


class SupportHoldOrder():
    def __init__(self, unit, supported):
        BaseOrder.__init__(self)
        self.unit = unit
        self.supported = supported
        self.key = (unit.key, SUP, supported.key)

    def __repr__(self):
        return "SupportHoldOrder(%s, %s)" % (repr(self.unit), repr(self.supported))

    def __str__(self):
        return "SupportHold(%s | %s)" % (self.unit, self.supported)

    def message(self):
        return (self.unit.wrap() ++ SUP + self.supported.wrap()).wrap()


class SupportMoveOrder():
    def __init__(self, unit, supported, destination):
        BaseOrder.__init__(self)
        self.unit = unit
        self.supported = supported
        self.dest = destination
        self.key = (unit.key, SUP, supported.key, MTO, destination)

    def __repr__(self):
        return "SupportMoveOrder(%s, %s, %s)" % (repr(self.unit), repr(self.supported), self.dest)

    def __str__(self):
        return "SupportMove(%s | %s -> %s)" % (self.unit, self.supported, self.dest)


class ConvoyOrder():
    def __init__(self, unit, cvy_unit, destination):
        BaseOrder.__init__(self)
        self.unit = unit
        self.cvy_unit = cvy_unit
        self.dest = destination
        self.key = (unit.key, CVY, cvy_unit.key, CTO, destination)

    def __repr__(self):
        return "ConvoyOrder(%s, %s)" % (repr(self.unit), repr(self.cvy_unit), self.dest)

    def __str__(self):
        return "Convoy(%s ^ %s -> %s)" % (self.unit, self.cvy_unit, self.dest)


class MoveByConvoyOrder():
    def __init__(self, unit, path):
        BaseOrder.__init__(self)
        self.unit = unit
        self.path = path

    def __repr__(self):
        raise NotImplementedError


class RetreatOrder():
    def __init__(self, unit, destination):
        BaseOrder.__init__(self)
        self.unit = unit
        self.dest = destination
        self.key = (unit.key, RTO, destination)

    def __repr__(self):
        return "RetreatOrder(%s, %s)" % (repr(self.unit), self.dest)

    def __str__(self):
        return "Retreat(%s -> %s)" % (self.unit, self.dest)

    def message(self):
        return (self.unit.wrap() ++ RTO ++ self.dest).wrap()


class DisbandOrder():
    def __init__(self, unit):
        BaseOrder.__init__(self)
        self.unit = unit
        self.key = (unit.key, DSB)

    def __repr__(self):
        return "DisbandOrder(%s)" % repr(self.unit)

    def __str__(self):
        return "Disband(%s)" % self.unit

    def message(self):
        return (self.unit.wrap() ++ DSB).wrap()


class BuildOrder():
    def __init__(self, unit):
        BaseOrder.__init__(self)
        self.unit = unit
        self.key = (unit.key, BLD)

    def __repr__(self):
        return "BuildOrder(%s)" % repr(self.unit)

    def __str__(self):
        return "Build(%s)" % self.unit

    def message(self):
        return (self.unit.wrap() ++ BLD).wrap()


class RemoveOrder():
    def __init__(self, unit):
        BaseOrder.__init__(self)
        self.unit = unit
        self.key = (unit.key, REM)

    def __repr__(self):
        return "RemoveOrder(%s)" % repr(self.unit)

    def __str__(self):
        return "Remove(%s)" % self.unit

    def message(self):
        return (self.unit.wrap() ++ REM).wrap()


class WaiveOrder():
    def __init__(self, power):
        BaseOrder.__init__(self)
        self.power = power
        self.key = (power, WVE)

    def __repr__(self):
        return "WaiveOrder(%s)" % self.power

    def __str__(self):
        return "Waive(%s)" % self.power

    def message(self):
        return (self.power + WVE).wrap()


if __name__ == '__main__':
    unit = Unit(RUS, FLT, [STP, SCS])
    h = HoldOrder(unit)
    print(h)
