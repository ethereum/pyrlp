import abc


class Atomic(type.__new__(abc.ABCMeta, 'metaclass', (), {})):
    """ABC for objects that can be RLP encoded as is."""
    pass


Atomic.register(str)
Atomic.register(bytes)
Atomic.register(bytearray)


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


def is_integer(value):
    return isinstance(value, int)


def safe_ord(c):
    try:
        return ord(c)
    except TypeError:
        assert isinstance(c, int)
        return c
