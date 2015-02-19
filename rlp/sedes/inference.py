from collections import Sequence
from functools import partial
from itertools import imap
from .lists import List, is_sedes
from .big_endian_int import big_endian_int
from .binary import binary


def infer_sedes(obj):
    """Try to find a sedes objects suitable for a given Python object.

    The sedes objects considered are `obj`'s class, `big_endian_int` and
    `binary`. If `obj` is a sequence, a :class:`ListSedes` will be constructed
    recursively.

    :param obj: the python object for which to find a sedes object
    :raises: :exc:`TypeError` if no appropriate sedes could be found
    """
    if is_sedes(obj.__class__):
        return obj.__class__
    if isinstance(obj, (int, long)) and obj >= 0:
        return big_endian_int
    if isinstance(obj, (str, unicode, bytearray)):
        return binary
    if isinstance(obj, Sequence):
        return List(imap(infer_sedes, obj))
    msg = 'Did not find sedes handling type {}'.format(type(obj).__name__)
    raise TypeError(msg)
