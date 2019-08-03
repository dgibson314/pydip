import struct

import init
import util


class Token():
    def __init__(self, _hex, tla):
        self._hex = _hex
        self.tla = tla

    def __call__(self, *args):
        return Message(self)(*args)

    def __pos__(self):
        '''
        >>> +ENG
        [Token(0x4101, ENG)]
        '''
        return Message(self)

    def __add__(self, other):
        return(Message(self) ++ other)

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
        raise NotImplementedError

    def __int__(self):
        return self._hex

    def __repr__(self):
        cat = self.get_category()
        if cat == 'TEXT':
            return 'Token(%s, %s)' % (self._hex, '\'' + self.tla + '\'')
        else:
            return 'Token(%s, %s)' % (self._hex, self.tla)

    def __str__(self):
        if self.tla == 'BRA':
            return '('
        elif self.tla == 'KET':
            return ')'
        else:
            return str(self.tla)

    def get_category(self):
        cat_byte = self._hex >> 8
        if (0x00 <= cat_byte <= 0x3F):
            category = 'INTEGER'
        elif (0x50 <= cat_byte <= 0x57):
            category = 'PROVINCE'
        else:
            category = init.categories[cat_byte]
        return category


class Message(list):
    def __init__(self, *args):
        for value in args:
            if isinstance(value, Token):
                self.append(value)
            elif isinstance(value, Message):
                self + value
            elif isinstance(value, int):
                try:
                    int_token = Token.integer(value)
                    self.append(int_token)
                except Exception:
                    pass
            elif isinstance(value, str):
                for c in value:
                    try:
                        ctoken = Token.char(c)
                        self.append(ctoken)
                    except Exception:
                        pass

    @classmethod
    def translate_from_bytes(cls, data):
        '''
        Should take in a Bytes object, and instantiate
        a Message instance of the corresponding Tokens.
        '''
        byte_lst = util.split_bytes_to_tokens(data)
        # Convert list of byte objects into list of corresponding integers.
        byte_lst = list(map(lambda x: int(x.hex(), 16), byte_lst))

        tokens = []
        for byte in byte_lst:
            cat_byte = byte >> 8
            if 0x00 <= cat_byte <= 0x3F:
                cat = 'INTEGER'
            elif 0x50 <= cat_byte <= 0x57:
                cat = 'PROVINCE'
            else:
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

    def __call__(self, *args):
        '''
        >>> msg = NME('name')('version')
        >>> msg.pretty_print()
        NME ( 'name' ) ( 'version' )
        >>> OBS().pretty_print()
        OBS ( )
        '''
        return self + Message(BRA) + Message(*args) + Message(KET)

    def __add__(self, *args):
        # TODO: can we do some more comprehensive error checking, please?
        '''
        >>> M = Message(YES, BRA)
        >>> N = Message(OBS, KET)
        >>> print(M + N)
        YES ( OBS )
        '''
        self.extend(*args)
        return self

    def __iadd__(self, token):
        self.extend(token)
        return self

    def wrap(self):
        return Message(BRA) + self + Message(KET)

    def raw_print(self):
        for token in self:
            print(token)

    def pack(self):
        return struct.pack('!' + 'H'*len(self), *map(int, self))

    def fold(self):
        '''
        >>> YES(OBS).fold()
        [Token(18460, YES), [Token(18447, OBS)]]
        >>> Message().fold()
        []
        >>> YES(MAP('standard')).fold()
        [Token(18460, YES), [Token(18441, MAP), ['standard']]]
        '''
        if self.count(BRA) != self.count(KET):
            raise ValueError('unbalanced parantheses')
        copy = list(self)
        while BRA in copy:
            k = copy.index(KET)
            b = self.rindex(copy[:k], BRA)
            copy[b:k+1] = [self.convert(copy[b+1:k])]
        return copy

    @staticmethod
    def rindex(lst, value):
        return len(lst) - list(reversed(lst)).index(value) - 1

    @staticmethod
    def convert(lst):
        result = []
        text = ''
        for token in lst:
            if not isinstance(token, Token):
                result.append(token)
            elif (token.get_category() == 'TEXT'):
                text += token.tla
            else:
                if (text != ''):
                    result.append(text)
                    text = ''
                if (token.get_category() == 'INTEGER'):
                    result.append(token._hex)
                else:
                    result.append(token)
        if text != '':
            result.append(text)
        return result

    def get_first_string(self):
        '''
        >>> msg = Message(MAP, BRA, "standard", KET)
        >>> print(msg.get_first_string())
        "standard"
        '''
        result = ''
        in_text = False
        for token in self:
            if token.get_category() == 'TEXT':
                in_text = True
                result += token.tla
            else:
                if in_text:
                    break
        return result

    def __repr__(self):
        result = 'Message('
        result += (", ".join([repr(x) for x in self]))
        result += ')'
        return result

    def __str__(self):
        result = ''
        string_msg = '\''

        for token in self:
            if (token.get_category() == 'TEXT'):
                string_msg += token.tla
            else:
                if (string_msg != '\''):
                    result += string_msg + '\' '
                    string_msg = '\''
                if (token.tla == 'BRA'):
                    result += '( '
                elif (token.tla == 'KET'):
                    result += ') '
                else:
                    result += str(token.tla) + ' '
        return result


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

# Unit Types
AMY = Token(0x4200, 'AMY')
FLT = Token(0x4201, 'FLT')

# Orders
CTO = Token(0x4320, 'CTO')
CVY = Token(0x4321, 'CVY')
HLD = Token(0x4322, 'HLD')
MTO = Token(0x4323, 'MTO')
SUP = Token(0x4324, 'SUP')
VTA = Token(0x4325, 'VIA')
DSB = Token(0x4340, 'DSB')
RTO = Token(0x4341, 'RTO')
BLD = Token(0x4380, 'BLD')
REM = Token(0x4381, 'REM')
WVE = Token(0x4382, 'WVE')

# Order Notes
MBV = Token(0x4400, 'MBV')
BPR = Token(0x4401, 'BPR')
CST = Token(0x4402, 'CST')
ESC = Token(0x4403, 'ESC')
FAR = Token(0x4404, 'FAR')
HSC = Token(0x4405, 'HSC')
NAS = Token(0x4406, 'NAS')
NMB = Token(0x4407, 'NMB')
NRN = Token(0x4409, 'NRN')
NRS = Token(0x440A, 'NRS')
NSA = Token(0x440B, 'NSA')
NSC = Token(0x440C, 'NSC')
NSF = Token(0x440D, 'NSF')
NSP = Token(0x440E, 'NSP')
NST = Token(0x440F, 'NST')
NSU = Token(0x4410, 'NSU')
NVR = Token(0x4411, 'NVR')
NYU = Token(0x4412, 'NYU')
YSC = Token(0x4413, 'YSC')

# Results
SUC = Token(0x4500, 'SUC')
BNC = Token(0x4501, 'BNC')
CUT = Token(0x4502, 'CUT')
DSR = Token(0x4503, 'DSR')
FLD = Token(0x4504, 'FLD')
NSO = Token(0x4505, 'NSO')
RET = Token(0x4506, 'RET')

# Coasts
NCS = Token(0x4600, 'NCS')
NEC = Token(0x4602, 'NEC')
ECS = Token(0x4604, 'ECS')
SEC = Token(0x4606, 'SEC')
SCS = Token(0x4608, 'SCS')
SWC = Token(0x460A, 'SWC')
WCS = Token(0x460C, 'WCS')
NWC = Token(0x460E, 'NWC')

# Phases
SPR = Token(0x4700, 'SPR')
SUM = Token(0x4701, 'SUM')
FAL = Token(0x4702, 'FAL')
AUT = Token(0x4703, 'AUT')
WIN = Token(0x4704, 'WIN')

# Commands
CCD = Token(0x4800, 'CCD')
DRW = Token(0x4801, 'DRW')
FRM = Token(0x4802, 'FRM')
GOF = Token(0x4803, 'GOF')
HLO = Token(0x4804, 'HLO')
HST = Token(0x4805, 'HST')
HUH = Token(0x4806, 'HUH')
IAM = Token(0x4807, 'IAM')
LOD = Token(0x4808, 'LOD')
MAP = Token(0x4809, 'MAP')
MDF = Token(0x480A, 'MDF')
MIS = Token(0x480B, 'MIS')
NME = Token(0x480C, 'NME')
NOT = Token(0x480D, 'NOT')
NOW = Token(0x480E, 'NOW')
OBS = Token(0x480F, 'OBS')
OFF = Token(0x4810, 'OFF')
ORD = Token(0x4811, 'ORD')
OUT = Token(0x4812, 'OUT')
PRN = Token(0x4813, 'PRN')
REJ = Token(0x4814, 'REJ')
SCO = Token(0x4815, 'SCO')
SLO = Token(0x4816, 'SLO')
SND = Token(0x4817, 'SND')
SUB = Token(0x4818, 'SUB')
SVE = Token(0x4819, 'SVE')
THX = Token(0x481A, 'THX')
TME = Token(0x481B, 'TME')
YES = Token(0x481C, 'YES')
ADM = Token(0x481D, 'ADM')

# Parameters
AOA = Token(0x4900, 'AOA')
BTL = Token(0x4901, 'BTL')
ERR = Token(0x4902, 'ERR')
LVL = Token(0x4903, 'LVL')
MRT = Token(0x4904, 'MRT')
MTL = Token(0x4905, 'MTL')
NPB = Token(0x4906, 'NPB')
NPR = Token(0x4907, 'NPR')
PDA = Token(0x4908, 'PDA')
PTL = Token(0x4909, 'PTL')
RTL = Token(0x490A, 'RTL')
UNO = Token(0x490B, 'UNO')
DSD = Token(0x490D, 'DSD')

# Press
ALY = Token(0x4A00, 'ALY')
AND = Token(0x4A01, 'AND')
BWX = Token(0x4A02, 'BWX')
DMZ = Token(0x4A03, 'DMZ')
ELS = Token(0x4A04, 'ELS')
EXP = Token(0x4A05, 'EXP')
FWD = Token(0x4A06, 'FWD')
FCT = Token(0x4A07, 'FCT')
FOR = Token(0x4A08, 'FOR')
HOW = Token(0x4A09, 'HOW')
IDK = Token(0x4A0A, 'IDK')
IFF = Token(0x4A0B, 'IFF')
INS = Token(0x4A0C, 'INS')
IOU = Token(0x4A0D, 'IOU')
OCC = Token(0x4A0E, 'OCC')
ORR = Token(0x4A0F, 'ORR')
PCE = Token(0x4A10, 'PCE')
POB = Token(0x4A11, 'POB')
PPT = Token(0x4A12, 'PPT')
PRP = Token(0x4A13, 'PRP')
QRY = Token(0x4A14, 'QRY')
SCD = Token(0x4A15, 'SCD')
SRY = Token(0x4A16, 'SRY')
SUG = Token(0x4A17, 'SUG')
THK = Token(0x4A18, 'THK')
THN = Token(0x4A19, 'THN')
TRY = Token(0x4A1A, 'TRY')
UOM = Token(0x4A1B, 'UOM')
VSS = Token(0x4A1C, 'VSS')
WHT = Token(0x4A1D, 'WHT')
WHY = Token(0x4A1E, 'WHY')
XDO = Token(0x4A1F, 'XDO')
XOY = Token(0x4A20, 'XOY')
YDO = Token(0x4A21, 'YDO')
WRT = Token(0x4A22, 'WRT')

# Provinces
# Inland non-SC
BOH = Token(0x5000, 'BOH')
BUR = Token(0x5001, 'BUR')
GAL = Token(0x5002, 'GAL')
RUH = Token(0x5003, 'RUH')
SIL = Token(0x5004, 'SIL')
TYR = Token(0x5005, 'TYR')
UKR = Token(0x5006, 'UKR')

# Inland SC
BUD = Token(0x5107, 'BUD')
MOS = Token(0x5108, 'MOS')
MUN = Token(0x5109, 'MUN')
PAR = Token(0x510A, 'PAR')
SER = Token(0x510B, 'SER')
VIE = Token(0x510C, 'VIE')
WAR = Token(0x510D, 'WAR')

# Sea non-SC
ADR = Token(0x520E, 'ADR')
AEG = Token(0x520F, 'AEG')
BAL = Token(0x5210, 'BAL')
BAR = Token(0x5211, 'BAR')
BLA = Token(0x5212, 'BLA')
EAS = Token(0x5213, 'EAS')
ECH = Token(0x5214, 'ECH')
GOB = Token(0x5215, 'GOB')
GOL = Token(0x5216, 'GOL')
HEL = Token(0x5217, 'HEL')
ION = Token(0x5218, 'ION')
IRI = Token(0x5219, 'IRI')
MAO = Token(0x521A, 'MAO')
NAO = Token(0x521B, 'NAO')
NTH = Token(0x521C, 'NTH')
NWG = Token(0x521D, 'NWG')
SKA = Token(0x521E, 'SKA')
TYS = Token(0x521F, 'TYS')
WES = Token(0x5220, 'WES')

# Coastal non-SC
ALB = Token(0x5421, 'ALB')
APU = Token(0x5422, 'APU')
ARM = Token(0x5423, 'ARM')
CLY = Token(0x5424, 'CLY')
FIN = Token(0x5425, 'FIN')
GAS = Token(0x5426, 'GAS')
LVN = Token(0x5427, 'LVN')
NAF = Token(0x5428, 'NAF')
PIC = Token(0x5429, 'PIC')
PIE = Token(0x542A, 'PIE')
PRU = Token(0x542B, 'PRU')
SYR = Token(0x542C, 'SYR')
TUS = Token(0x542D, 'TUS')
WAL = Token(0x542E, 'WAL')
YOR = Token(0x542F, 'YOR')

# Coastal SC
ANK = Token(0x5530, 'ANK')
BEL = Token(0x5531, 'BEL')
BER = Token(0x5532, 'BER')
BRE = Token(0x5533, 'BRE')
CON = Token(0x5534, 'CON')
DEN = Token(0x5535, 'DEN')
EDI = Token(0x5536, 'EDI')
GRE = Token(0x5537, 'GRE')
HOL = Token(0x5538, 'HOL')
KIE = Token(0x5539, 'KIE')
LON = Token(0x553A, 'LON')
LVP = Token(0x553B, 'LVP')
MAR = Token(0x553C, 'MAR')
NAP = Token(0x553D, 'NAP')
NWY = Token(0x553E, 'NWY')
POR = Token(0x553F, 'POR')
ROM = Token(0x5540, 'ROM')
RUM = Token(0x5541, 'RUM')
SEV = Token(0x5542, 'SEV')
SMY = Token(0x5543, 'SMY')
SWE = Token(0x5544, 'SWE')
TRI = Token(0x5545, 'TRI')
TUN = Token(0x5546, 'TUN')
VEN = Token(0x5547, 'VEN')

# Bicoastal SC
BUL = Token(0x5748, 'BUL')
SPA = Token(0x5749, 'SPA')
STP = Token(0x574A, 'STP')


representation = {
    BRA, KET,
    AUS, ENG, FRA, GER, ITA, RUS, TUR,
    AMY, FLT,
    CTO, CVY, HLD, MTO, SUP, VTA, DSB, RTO, BLD, REM, WVE,
    MBV, BPR, CST, ESC, FAR, HSC, NAS, NMB, NRN, NRS, NSA, NSC, NSF, NSP, NST, NSU, NVR, NYU, YSC,
    SUC, BNC, CUT, DSR, FLD, NSO, RET,
    NCS, NEC, ECS, SEC, SCS, SWC, WCS, NWC,
    SPR, SUM, FAL, AUT, WIN,
    CCD, DRW, FRM, GOF, HLO, HST, HUH, IAM, LOD, MAP, MDF, MIS, NME, NOT, NOW, OBS, OFF, ORD, OUT, PRN, REJ, SCO, SLO, SND, SUB, SVE, THX, TME, YES, ADM,
    AOA, BTL, ERR, LVL, MRT, MTL, NPB, NPR, PDA, PTL, RTL, UNO, DSD,
    ALY, AND, BWX, DMZ, ELS, EXP, FWD, FCT, FOR, HOW, IDK, IFF, INS, IOU, OCC, ORR, PCE, POB, PPT, PRP, QRY, SCD, SRY, SUG, THK, THN, TRY, UOM, VSS, WHT, WHY, XDO, XOY, YDO, WRT,
    BOH, BUR, GAL, RUH, SIL, TYR, UKR,
    BUD, MOS, MUN, PAR, SER, VIE, WAR,
    ADR, AEG, BAL, BAR, BLA, EAS, ECH, GOB, GOL, HEL, ION, IRI, MAO, NAO, NTH, NWG, SKA, TYS, WES,
    ALB, APU, ARM, CLY, FIN, GAS, LVN, NAF, PIC, PIE, PRU, SYR, TUS, WAL, YOR,
    ANK, BEL, BER, BRE, CON, DEN, EDI, GRE, HOL, KIE, LON, LVP, MAR, NAP, NWY, POR, ROM, RUM, SEV, SMY, SWE, TRI, TUN, VEN,
    BUL, SPA, STP,
}
