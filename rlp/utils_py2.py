import abc
import struct


class Atomic(object):

    """ABC for objects that can be RLP encoded as is."""
    __metaclass__ = abc.ABCMeta


Atomic.register(str)
Atomic.register(bytearray)
Atomic.register(unicode)

str_to_bytes = bytes_to_str = str
ascii_chr = chr


def int_to_big_endian(value):
    cs = []
    while value > 0:
        cs.append(chr(value % 256))
        value /= 256
    s = ''.join(reversed(cs))
    return s


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
    if not isinstance(s, (str, unicode)):
        raise TypeError('Value must be an instance of str or unicode')
    return s.decode('hex')


def encode_hex(s):
    if not isinstance(s, (str, unicode)):
        raise TypeError('Value must be an instance of str or unicode')
    return s.encode('hex')


safe_ord = ord
