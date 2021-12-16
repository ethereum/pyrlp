from abc import ABC, abstractmethod
from typing import Any, List

from rlp.exceptions import (
    ObjectDeserializationError,
    ObjectSerializationError,
)


class DynamicSerializable(ABC):
    @property
    @abstractmethod
    def sedes_options(self) -> List:
        ...

    @classmethod
    def deserialize(cls, obj: Any) -> bytes:
        for sedes in cls.sedes_options:
            try:
                return sedes.deserialize(obj)
            except ObjectDeserializationError:
                pass

    @classmethod
    def serialize(cls, obj: Any) -> bytes:
        for sedes in cls.sedes_options:
            try:
                return sedes.serialize(obj)
            except ObjectSerializationError:
                pass
