from collections import Sequence
from functools import partial
from itertools import imap
from .sedes.lists import ListSedes, Serializable


def infer_sedes(obj, sedes_list):
    """Try to find a sedes suitable for a given Python object.

    If ``obj`` is :class:`rlp.Serializable` this will always return the class
    of ``obj``. If ``obj`` is a sequence, a :class:`ListSedes` will be
    constructed recursively.
    
    :param obj: the python object in question
    :param sedes_list: the collection of sedes objects to check
    :raises TypeError: if no appropriate sedes could be found
    """
    if isinstance(obj, Serializable):
        return obj.__class__
    for sedes in sedes_list:
        if sedes.serializable(obj):
            return sedes
    if isinstance(obj, Sequence):
        return ListSedes(imap(partial(infer_sedes, sedes_list=sedes_list), obj))
    msg = 'Did not find sedes handling type {}'.format(type(obj).__name__)
    raise TypeError(msg)
