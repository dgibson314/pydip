import struct

import init

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
        msg = ''

        for token in self:
            if (token.tla == 'BRA'):
                msg += ' ( '
            elif (token.tla == 'KET'):
                msg += ' ) '
            else:
                msg += token.tla + ' '

        print(msg)

