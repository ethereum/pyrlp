from ..exceptions import SerializationError, DeserializationError


class Binary(object):
    """A sedes object for binary data of certain length.
    
    :param min_length: the minimal length in bytes or `None` for no lower limit
    :param max_length: the maximal length in bytes or `None` for no upper limit
    """

    def __init__(self, min_length=None, max_length=None):
        self.min_length = min_length or 0
        self.max_length = max_length or float('inf')

    @classmethod
    def fixed_length(cls, l):
        """Create a sedes for binary data with exactly `l` bytes."""
        return cls(l, l)

    def serialize(self, obj):
        if not isinstance(obj, (str, unicode, bytearray)):
            raise SerializationError('Object is not a string', obj)
        if not self.min_length <= len(str(obj)) <= self.max_length:
            raise SerializationError('String has invalid length', obj)
        return str(obj)

    def deserialize(self, serial):
        b = str(serial)
        if self.min_length <= len(b) <= self.max_length:
            return b
        else:
            raise DeserializationError('String has invalid length', serial)


binary = Binary()
