class Gameboard():
    '''
    Stores info about current turn and current unit positions.
        - powers        List of powers
        - provinces     Dictionary of powers mapped to home SCs, and a list on non-SCs
        - adjacencies   
    '''
    def __init__(self, MDF_message):
        self.powers = []
        self.provinces = {}
        self.adjacencies = []

        folded_msg = MDF_message.fold()

        # Adding powers
        for power in folded_msg[1]:
            self.powers.append(power)

        # Adding supply centers
        sc_section = folded_msg[2][0]
        for sc_lst in sc_section:
            power = sc_lst[0]
            self.provinces[power] = sc_lst[1:]

        # Adding non-SCs
        self.provinces['Non-SC'] = []
        non_sc_section = folded_msg[2][1]
        for province in non_sc_section:
            self.provinces['Non-SC'].append(province)

        # Adding adjacencies 
        adjacencies = folded_msg[3]
