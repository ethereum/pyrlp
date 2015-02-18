from . import big_endian_int

class FixedLengthInt(object):
    """A sedes for big endian integers of fixed length.

    :param l: the length in bytes
    """

    def __init__(self, l):
        self.l = l

    def serializable(self, obj):
        return big_endian_int.serializable(obj) and obj < 256**self.l

    def serialize(self, obj):
        s = big_endian_int.serialize(obj)
        return '\x00' * max(0, self.l - len(s)) + s

    def deserialize(self, serial):
        if len(serial) != self.l:
            raise DeserializationError('Invalid size', serial)
        return big_endian_int.deserialize(serial.lstrip('\x00'))
