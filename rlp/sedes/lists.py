"""Module for sedes objects that use lists as serialization format."""


from collections import Sequence
from functools import partial
from itertools import izip, imap


class class_property(property):
    """same as ``property`` but for classmethods"""
    # see http://stackoverflow.com/a/1383402

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


def is_sedes(obj):
    """Check if `obj` is a sedes object.
    
    A sedes object is characterized by having the methods `serialize(obj)`,
    `serializable(obj)` and `deserialize(serial)`.
    """
    methods = ('serialize', 'deserialize', 'serializable')
    return all(hasattr(obj, m) for m in methods)


class ListSedes(list):
    """A sedes for lists, implemented as a list of other sedes objects."""

    def __init__(self, elements=[]):
        super(ListSedes, self).__init__()
        for e in elements:
            if is_sedes(e):
                self.append(e)
            elif isinstance(e, Sequence):
                self.append(ListSedes(e))
            else:
                raise TypeError('Instances of ListSedes must only contain '
                                'sedes objects or sequences thereof.')

    def serializable(self, obj):
        if not isinstance(obj, Sequence) or len(self) != len(obj):
            return False
        return all(sedes.serializable(element)
                   for element, sedes in izip(obj, self))

    def serialize(self, obj):
        return [sedes.serialize(element)
                for element, sedes in izip(obj, self)]

    def deserialize(self, serial):
        return [sedes.deserialize(element) 
                for element, sedes in izip(serial, self)]


class Serializable(object):
    """Base class for objects which can be serialized into RLP lists."""

    fields = tuple()

    def __init__(self, *args, **kwargs):
        # check number of arguments
        got = 1 + len(args) + len(kwargs)
        expected = 1 + len(self.fields)
        if got != expected:
            raise TypeError('Wrong number of arguments given (expected {0}, '
                            'got {1})'.format(expected, got))

        # check keyword arguments are known
        field_set = set(field for field, _ in self.fields)
        for field, _ in kwargs.iteritems():
            if field not in field_set:
                raise TypeError('Unknown keyword argument: {}'.format(field))
        
        # set positional arguments
        for (field, _), arg in izip(self.fields, args):
            setattr(self, field, arg)
            field_set.remove(field)

        # set keyword arguments, if not already set
        for (field, value) in kwargs.iteritems():
            if field in field_set:
                setattr(self, field, value)
                field_set.remove(field)
            else:
                raise TypeError('Got argument {0} more than '
                                'once'.format(field))

    def __eq__(self, other):
        """Two objects are equal, if they are equal after serialization."""
        if not hasattr(other.__class__, 'serialize'):
            return False
        return self.serialize(self) ==other.serialize(other)


    @class_property
    @classmethod
    def sedes(cls):
        return ListSedes(sedes for _, sedes in cls.fields)

    @classmethod
    def serializable(cls, obj):
        if not hasattr(obj, 'fields') or obj.fields != cls.fields:
            return False
        return all(sedes.serializable(getattr(obj, field))
                   for field, sedes in cls.fields)

    @classmethod
    def serialize(cls, obj):
        field_values = [getattr(obj, field) for field, _ in cls.fields]
        return cls.sedes.serialize(field_values)

    @classmethod
    def deserialize(cls, serial):
        values = cls.sedes.deserialize(serial)
        params = {field: value for (field, _), value
                               in izip(cls.fields, values)}
        return cls(**params)
