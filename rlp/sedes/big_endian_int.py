"""A sedes for unsigned big endian integers."""


from ..exceptions import SerializationError, DeserializationError


def serializable(obj):
    return isinstance(obj, (int, long)) and obj >= 0


def serialize(obj):
    if obj == 0:
        return '\x00'
    digits = ()
    cs = []
    while obj > 0:
        cs.append(chr(obj % 256))
        obj /= 256
    return ''.join(reversed(cs))


def deserialize(serial):
    if len(serial) == 0:
        raise DeserializationError('Invalid serialization (empty string)',
                                   serial)
    if serial[0] == '\x00' and len(serial) != 1:
        raise DeserializationError('Invalid serialization (not minimal length)',
                                   serial)
    return reduce(lambda v, d: v * 256 + ord(d), serial, 0)
