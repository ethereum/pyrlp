import abc


class Atomic(object):

    """ABC for objects that can be RLP encoded as is."""
    __metaclass__ = abc.ABCMeta


Atomic.register(str)
Atomic.register(bytearray)
Atomic.register(unicode)

str_to_bytes = bytes_to_str = lambda a: a


def ascii_chr(value):
    return chr(value)


def int_to_big_endian(value):
    cs = []
    while value > 0:
        cs.append(chr(value % 256))
        value /= 256
    s = ''.join(reversed(cs))
    return s


def is_integer(value):
    return isinstance(value, (int, long))


def bytes_to_int_array(value):
    return memoryview(value).tolist()


def decode_hex(s):
    if not isinstance(s, (str, unicode)):
        raise TypeError('Value must be an instance of str or unicode')
    return s.decode('hex')


def encode_hex(s):
    if not isinstance(s, (str, unicode)):
        raise TypeError('Value must be an instance of str or unicode')
    return s.encode('hex')
