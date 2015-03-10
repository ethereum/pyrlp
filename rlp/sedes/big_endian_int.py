from ..exceptions import DeserializationError, SerializationError


class BigEndianInt(object):
    """A sedes for big endian integers.

    :param l: the size of the serialized representation in bytes or `None` to
              use the shortest possible one
    """

    def __init__(self, l=None):
        self.l = l

    def serialize(self, obj):
        if not isinstance(obj, (int, long)):
            raise SerializationError('Can only serialize integers', obj)
        if self.l is not None and obj >= 256**self.l:
            raise SerializationError('Integer too large (does not fit in {} '
                                     'bytes)'.format(self.l), obj)
        if obj < 0:
            raise SerializationError('Cannot serialize negative integers', obj)

        cs = []
        while obj > 0:
            cs.append(chr(obj % 256))
            obj /= 256
        s = ''.join(reversed(cs))

        if self.l is not None:
            return '\x00' * max(0, self.l - len(s)) + s
        else:
            return s

    def deserialize(self, serial):
        if self.l is not None and len(serial) != self.l:
            raise DeserializationError('Invalid serialization (wrong size)',
                                       serial)
        if self.l is None and len(serial) > 1 and serial[0] == '\x00':
            raise DeserializationError('Invalid serialization (not minimal '
                                       'length)', serial)
        return int(serial.encode('hex') or '0', 16)


big_endian_int = BigEndianInt()
