import struct
from pyConst import *

hubType = 'Custom'

port_lut = { 0: '0',
             1: '1',
             2: '2',}

DEVICE_MESSAGE_MAP = {  # B = u8, b = i8, H = u16, h = i16, i = i32
    0x00: ("hub info",       "<BBB",    ['Battery','USB']),
    0x01: ("vision sensor",  "<HHBBB",  ['x', 'y', 'red', 'green', 'blue']),
}

INFO_MESSAGE = [
    ("RPC",      "<BBH", ['major','minor','build']),
    ("Firmware", "<BBH", ['major','minor','build']),
    ("MaxSize",  "<HHH", ['packet','message','chunk']),
    ("GroupID",  "<H",   None),
]

commands = {
    'info':         ('<B',     INFO_REQUEST, None),
    'feed':         ('<BH',    DEVICE_NOTIFICATION_REQUEST, {'values':{'updateTime':1000}}),
}

TO_HIDE = []

##### no need for packing and unpacking with tech elements
def pack(message):
    return message

def unpack(message):
    return bytes(message)
