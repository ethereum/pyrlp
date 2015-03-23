class RLPException(Exception):
    """Base class for exceptions raised by this package."""
    pass


class EncodingError(RLPException):
    """Exception raised if encoding fails.

    :ivar obj: the object that could not be encoded
    """

    def __init__(self, message, obj):
        super(EncodingError, self).__init__(message)
        self.obj = obj


class DecodingError(RLPException):
    """Exception raised if decoding fails.

    :ivar rlp: the RLP string that could not be decoded
    """

    def __init__(self, message, rlp):
        super(DecodingError, self).__init__(message)
        self.rlp = rlp


class SerializationError(RLPException):
    """Exception raised if serialization fails.

    :ivar obj: the object that could not be serialized
    """

    def __init__(self, message, obj):
        super(SerializationError, self).__init__(message)
        self.obj = obj


class DeserializationError(RLPException):
    """Exception raised if deserialization fails.

    :ivar serial: the decoded RLP string that could not be deserialized
    """

    def __init__(self, message, serial):
        super(DeserializationError, self).__init__(message)
        self.serial = serial
