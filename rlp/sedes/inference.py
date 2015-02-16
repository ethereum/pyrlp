from collections import Sequence
from functools import partial
from itertools import imap
from . import sedes_list
from .lists import ListSedes, is_sedes


def infer_sedes(obj, sedes_list):
    """Try to find a sedes objects suitable for a given Python object.

    The sedes objects considered are `obj`'s class and all elements of
    `sedes_list`. If `obj` is a sequence, a :class:`ListSedes` will be
    constructed recursively.
    
    :param obj: the python object for which to find a sedes object
    :param sedes_list: a collection of sedes objects to check
    :raises TypeError: if no appropriate sedes could be found
    """
    if is_sedes(obj.__class__):
        return obj.__class__
    for sedes in sedes_list:
        if sedes.serializable(obj):
            return sedes
    if isinstance(obj, Sequence):
        return ListSedes(imap(partial(infer_sedes, sedes_list=sedes_list), obj))
    msg = 'Did not find sedes handling type {}'.format(type(obj).__name__)
    raise TypeError(msg)
