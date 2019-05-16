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

class TokenMessage():
    def __init__(self, tlist):
        self.tokens = tlist











