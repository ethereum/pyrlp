from typing import Union, Any

from rlp.exceptions import SerializationError, DeserializationError
from rlp.atomic import Atomic


class Binary(object):
    """A sedes object for binary data of certain length.

    :param min_length: the minimal length in bytes or `None` for no lower limit
    :param max_length: the maximal length in bytes or `None` for no upper limit
    :param allow_empty: if true, empty strings are considered valid even if
                        a minimum length is required otherwise
    """

    def __init__(self,
                 min_length: int = None,
                 max_length: int = None,
                 allow_empty: bool = False) -> None:
        self.min_length = min_length or 0
        if max_length is None:
            self.max_length = float('inf')
        else:
            self.max_length = max_length
        self.allow_empty = allow_empty

    @classmethod
    def fixed_length(cls, length: int, allow_empty: bool = False) -> 'Binary':
        """Create a sedes for binary data with exactly ``length`` bytes."""
        return cls(length, length, allow_empty=allow_empty)

    @classmethod
    def is_valid_type(cls, obj: Any) -> bool:
        return isinstance(obj, (bytes, bytearray))

    def is_valid_length(self, length: int) -> bool:
        return any((self.min_length <= length <= self.max_length,
                    self.allow_empty and length == 0))

    def serialize(self, obj: Union[bytes, bytearray]) -> bytes:
        if not Binary.is_valid_type(obj):
            raise SerializationError('Object is not a serializable ({})'.format(type(obj)), obj)

        if not self.is_valid_length(len(obj)):
            raise SerializationError('Object has invalid length', obj)

        return obj

    def deserialize(self, serial: bytes) -> bytes:
        if not isinstance(serial, Atomic):
            m = 'Objects of type {} cannot be deserialized'
            raise DeserializationError(m.format(type(serial).__name__), serial)

        if self.is_valid_length(len(serial)):
            return serial
        else:
            raise DeserializationError('{} has invalid length'.format(type(serial)), serial)


binary = Binary()
