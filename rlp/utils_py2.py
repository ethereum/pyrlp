import abc
import struct
import codecs
import binascii


class Atomic(object):

    """ABC for objects that can be RLP encoded as is."""
    __metaclass__ = abc.ABCMeta


Atomic.register(str)
Atomic.register(bytearray)
Atomic.register(unicode)

bytes_to_str = str
ascii_chr = chr


def str_to_bytes(value):
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    elif isinstance(value, unicode):
        return codecs.encode(value, 'utf8')
    else:
        raise TypeError("Value must be text, bytes, or bytearray")


def _old_int_to_big_endian(value):
    cs = []
    while value > 0:
        cs.append(chr(value % 256))
        value /= 256
    s = ''.join(reversed(cs))
    return s


def packl(lnum):
    if lnum == 0:
        return b'\0'
    s = hex(lnum)[2:]
    s = s.rstrip('L')
    if len(s) & 1:
        s = '0' + s
    s = binascii.unhexlify(s)
    return s

int_to_big_endian = packl


def big_endian_to_int(value):
    if len(value) == 1:
        return ord(value)
    elif len(value) <= 8:
        return struct.unpack('>Q', value.rjust(8, '\x00'))[0]
    else:
        return int(encode_hex(value), 16)


def is_integer(value):
    return isinstance(value, (int, long))


def decode_hex(s):
    if isinstance(s, bytearray):
        s = str(s)
    if not isinstance(s, (str, unicode)):
        raise TypeError('Value must be an instance of str or unicode')
    return s.decode('hex')


def encode_hex(s):
    if isinstance(s, bytearray):
        s = str(s)
    if not isinstance(s, (str, unicode)):
        raise TypeError('Value must be an instance of str or unicode')
    return s.encode('hex')


def safe_ord(s):
    if isinstance(s, int):
        return s
    return ord(s)
