import abc


class Atomic(object):
    """ABC for objects that can be RLP encoded as is."""
    __metaclass__ = abc.ABCMeta


Atomic.register(str)
Atomic.register(bytearray)
