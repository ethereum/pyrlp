"""A sedes for unsigned big endian integers."""


from ..exceptions import SerializationError, DeserializationError


def serializable(obj):
    return isinstance(obj, (int, long)) and obj >= 0


def serialize(obj):
    digits = ()
    cs = []
    while obj > 0:
        cs.append(chr(obj % 256))
        obj /= 256
    return ''.join(reversed(cs))


def deserialize(serial):
    if len(serial) > 1 and serial[0] == '\x00':
        raise DeserializationError('Invalid serialization (not minimal length)',
                                   serial)
    return reduce(lambda v, d: v * 256 + ord(d), serial, 0)
