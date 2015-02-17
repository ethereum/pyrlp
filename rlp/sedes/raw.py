"""
A sedes that does nothing. Thus, everything that can be directly encoded by RLP
is serializable. This sedes can be used as a placeholder when deserializing
larger structures.
"""


from collections import Sequence
from ..codec import Atomic


def serializable(obj):
    if isinstance(obj, Atomic):
        return True
    elif isinstance(obj, Sequence):
        return all(serializable(e) for e in obj)
    else:
        return False


def serialize(obj):
    return obj


def deserialize(serial):
    return serial
