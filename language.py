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
    def char(cls, char):
        return cls(0x4B00 + ord(char), char)

    @classmethod
    def ascii(cls, _ascii):
        return cls(0x4B00 + _ascii, chr(_ascii))

    @classmethod
    def byte(cls, _byte):
        pass

    def __int__(self):
        return self._hex

    def get_category(self):
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
                for c in token:
                    try:
                        ctoken = Token.char(c)
                        self.append(ctoken)
                    except:
                        pass

    @classmethod
    def translate_from_bytes(cls, data):
        '''
        Should take in a Bytes object, and instantiate
        a Message instance of the corresponding Tokens.
        '''
        byte_lst = util.split_bytes_to_tokens(data)
        # Convert list of byte objects into list of corresponding
        # integers.
        byte_lst = list(map(lambda x: int(x.hex(), 16), byte_lst))
        
        tokens = []
        for byte in byte_lst:
            cat = init.categories[byte >> 8]
            token = None
            if (cat == 'INTEGER'):
                token = (Token.integer(byte & 0x00ff))
            elif (cat == 'TEXT'):
                token = (Token.ascii(byte & 0x00ff))
            else:
                for t in representation:
                    if t._hex == byte:
                        token = t
            if token is None:
                # TODO: exception handling?
                print("BAD")
            else:
                tokens.append(token)
        return cls(*tokens)

    def raw_print(self):
        for token in self:
            token.raw_print()
    
    def pack(self):
        return struct.pack('!' + 'H'*len(self), *map(int, self))

    def pretty_print(self):
        msg = ''
        string_msg = '\''

        for token in self:
            if (token.get_category() == 'TEXT'):
                string_msg += token.tla
            else:
                if (string_msg != '\''):
                    msg += string_msg + '\' '
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

    MAP,
    OBS,
    YES,
}
