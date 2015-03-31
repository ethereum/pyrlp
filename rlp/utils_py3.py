import abc
import binascii
from math import ceil


class Atomic(metaclass = abc.ABCMeta):
    """ABC for objects that can be RLP encoded as is."""
    pass


Atomic.register(str)
Atomic.register(bytes)


def str_to_bytes(value):
    if isinstance(value, bytearray):
        value = bytes(value)
    if isinstance(value, bytes):
        return value
    return bytes(value, 'utf-8')


def bytes_to_str(value):
    if isinstance(value, str):
        return value
    return value.decode('utf-8')


def ascii_chr(value):
    return bytes([value])


def int_to_big_endian(value):
    byte_length = ceil(value.bit_length() / 8)
    return (value).to_bytes(byte_length, byteorder='big')


def is_integer(value):
    return isinstance(value, int)


def bytes_to_int_array(value):
    return value


def decode_hex(s):
    if isinstance(s, str):
        return bytes.fromhex(s)
    if isinstance(s, bytes):
        return binascii.unhexlify(s)
    raise TypeError('Value must be an instance of str or bytes')


def encode_hex(b):
    if isinstance(b, str):
        b = bytes(b, 'utf-8')
    if isinstance(b, bytes):
        return binascii.hexlify(b)
    raise TypeError('Value must be an instance of str or bytes')
