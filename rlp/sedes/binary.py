class Binary(object):
    """A sedes object for binary data of certain length.
    
    :param min_length: the minimal length in bytes or `None` for no lower limit
    :param max_length: the maximal length in bytes or `None` for no upper limit
    """

    @classmethod
    def fixed_length(cls, l):
        """Create a sedes for binary data with exactly `l` bytes."""
        return cls(l, l)


    def __init__(self, min_length=None, max_length=None):
        if min_length:
            self.min_length = min_length
        else:
            self.min_length = 0
        if max_length:
            self.max_length = max_length
        else:
            self.max_length = float('inf')

    def serializable(self, obj):
        if not isinstance(obj, (str, bytearray)):
            return False
        return self.min_length <= len(str(obj)) <= self.max_length

    def serialize(self, obj):
        return str(obj)

    def deserialize(self, serial):
        b = str(serial)
        if not self.min_length <= len(b) <= self.max_length:
            return b
