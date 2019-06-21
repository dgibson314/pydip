class Gameboard():
    '''
    Stores info about current turn and current unit positions.

    The following instance variables refer to the initial game state, and will
    remain unchanged throughout the game.
    - powers        List of powers
    - home_centers  Dictionary of powers mapped to their home SCs
    - adjacencies   Mimics the structure of MDF adjacency list, e.g. [[prov_adj][prov_adj]...],
                    where [prov_adj] is of the form 
                    [province [unit_type adj_prov adj_prov...]...]...].
                    See the DAIDE Message Syntax section on the MDF message
                    for more details.

    The following instance variables are updated as the game progresses, 
    (probably) by being passed NOW and SCO messages from the DAIDE server.
    - supply_centers    Mapping from powers to a list of SCs they have 
                        after each Fall Retreat turn
    - units             

    '''
    def __init__(self, MDF_message):
        self.powers = []
        self.home_centers = {}
        self.adjacencies = {}

        self.supply_centers = {}
        self.units = {}
        self.year = None
        self.season = None

        folded_msg = MDF_message.fold()

        # Adding powers
        for power in folded_msg[1]:
            self.powers.append(power)

        # Adding supply centers
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
        ''' Updates the current supply center ownership by traversing
        an SCO message from DAIDE server. Unowned centers are listed against
        the power name UNO.
        '''
        folded_SCO = SCO_message.fold()
        for position in folded_SCO[1:]:
            power = position[0]
            centers = position[1:]
            self.supply_centers[power] = []
            for center in centers:
                self.supply_centers[power].append(center)
