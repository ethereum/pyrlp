"""A Sedes for textual data.

This serializes and deserializes unicode strings with UTF-8.
"""


def serializable(obj):
    return isinstance(obj, (str, bytearray, unicode))


def serialize(obj):
    return unicode(obj).encode('utf-8')


def deserialize(code):
    return code.decode('utf-8')
