import struct

import init
import util

class Token():
    def __init__(self, _hex, tla):
        self._hex = _hex
        self.tla = tla

    @classmethod
    def integer(cls, _int):
        return cls(0x0000 + _int, _int)

    @classmethod
    def ascii(cls, _char):
        return cls(0x4B00 + ord(_char), _char)

    @classmethod
    def byte(cls, _byte):
        pass

    def __int__(self):
        return self._hex

    def get_category(self):
        # Get MSB byte
        cat_byte = self._hex >> 8
        category = init.categories[cat_byte]
        return category

    def raw_print(self):
        result = 'Token(' 
        result += hex(self._hex) + ', ' + self.tla + ')'
        print(result)

    def pretty_print(self):
        cat = self.get_category()
        
        if (cat == 'BRACKET'):
            if (self.tla == 'BRA'):
                print('(')
            else:
                print(')')
        else:
            print(self.tla)


class Message(list):
    def __init__(self, *argv):
        for token in argv:
            if isinstance(token, Token):
                self.append(token)
            elif isinstance(token, int):
                try:
                    int_token = Token.integer(token)
                    self.append(int_token)
                except:
                    pass
            elif isinstance(token, str):
                result = []
                for c in token:
                    try:
                        ctoken = Token.ascii(c)
                        result.append(ctoken)
                    except:
                        pass
                self.append(result)

    @classmethod
    def translate_from_bytes(cls, data):
        '''
        Should take in a Bytes object, and instantiate
        a Message instance of the corresponding Tokens.
        '''
        #TODO: handle ASCII and integers
        byte_lst = util.split_bytes_to_tokens(data)
        # Convert list of byte objects into list of corresponding
        # integers.
        byte_lst = list(map(lambda x: int(x.hex(), 16), byte_lst))
        
        tokens = []
        for byte in byte_lst:
            for token in representation:
                if token._hex == byte:
                    tokens.append(token)
        return cls(*tokens)

    def raw_print(self):
        flattened = self.flatten()
        for token in flattened:
            token.raw_print()

    def flatten(self):
        flat_list = []
        for token in self:
            if isinstance(token, list):
                for c in token:
                    flat_list.append(c)
            flat_list.append(token)
        return flat_list

    def pack(self):
        flattened = self.flatten()
        return struct.pack('!' + 'H'*len(flattened), *map(int, flattened))

    def pretty_print(self):
        #TODO: handle strings
        msg = ''

        for token in self:
            if (token.tla == 'BRA'):
                msg += '( '
            elif (token.tla == 'KET'):
                msg += ') '
            else:
                msg += token.tla + ' '

        print(msg)



# Brackets
BRA = Token(0x4000, 'BRA')
KET = Token(0x4001, 'KET')

# Powers
AUS = Token(0x4100, 'AUS')
ENG = Token(0x4101, 'ENG')
FRA = Token(0x4102, 'FRA')
GER = Token(0x4103, 'GER')
ITA = Token(0x4104, 'ITA')
RUS = Token(0x4105, 'RUS')
TUR = Token(0x4106, 'TUR')

# Commands
HLO = Token(0x4804, 'HLO')
IAM = Token(0x4807, 'IAM')
MAP = Token(0x4809, 'MAP')
OBS = Token(0x480F, 'OBS')
NME = Token(0x480C, 'NME')
YES = Token(0x481C, 'YES')

representation = {
    BRA,
    KET,
    YES,
    OBS,
}

msg = b'H\x1c@\x00H\x0f@\x01'
m = Message.translate_from_bytes(msg)
m.pretty_print()
