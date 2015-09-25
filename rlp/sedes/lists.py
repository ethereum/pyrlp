"""Module for sedes objects that use lists as serialization format."""
import sys
from collections import Sequence
from itertools import count
from ..exceptions import (SerializationError, ListSerializationError, ObjectSerializationError,
                          DeserializationError, ListDeserializationError,
                          ObjectDeserializationError)
from ..sedes.binary import Binary as BinaryClass

if sys.version_info.major == 2:
    from itertools import izip as zip


def is_sedes(obj):
    """Check if `obj` is a sedes object.

    A sedes object is characterized by having the methods `serialize(obj)` and
    `deserialize(serial)`.
    """
    # return all(hasattr(obj, m) for m in ('serialize', 'deserialize'))
    return hasattr(obj, 'serialize') and hasattr(obj, 'deserialize')


def is_sequence(obj):
    """Check if `obj` is a sequence, but not a string or bytes."""
    return isinstance(obj, Sequence) and not BinaryClass.is_valid_type(obj)


class List(list):

    """A sedes for lists, implemented as a list of other sedes objects.

    :param strict: If true (de)serializing lists that have a length not
                   matching the sedes length will result in an error. If false
                   (de)serialization will stop as soon as either one of the
                   lists runs out of elements.
    """

    def __init__(self, elements=[], strict=True):
        super(List, self).__init__()
        self.strict = strict
        for e in elements:
            if is_sedes(e):
                self.append(e)
            elif isinstance(e, Sequence):
                self.append(List(e))
            else:
                raise TypeError('Instances of List must only contain sedes '
                                'objects or nested sequences thereof.')

    def serialize(self, obj):
        if not is_sequence(obj):
            raise ListSerializationError('Can only serialize sequences', obj)
        if self.strict and len(self) != len(obj) or len(self) < len(obj):
            raise ListSerializationError('List has wrong length', obj)
        result = []
        for index, (element, sedes) in enumerate(zip(obj, self)):
            try:
                result.append(sedes.serialize(element))
            except SerializationError as e:
                raise ListSerializationError(obj=obj, element_exception=e, index=index)
        return result

    def deserialize(self, serial):
        if not is_sequence(serial):
            raise ListDeserializationError('Can only deserialize sequences', serial)
        result = []
        element_iterator = iter(serial)
        sedes_iterator = iter(self)
        elements_consumed = False
        sedes_consumed = False
        for index in count():
            try:
                element = next(element_iterator)
            except StopIteration:
                elements_consumed = True
            try:
                sedes = next(sedes_iterator)
            except StopIteration:
                sedes_consumed = True
            if not (sedes_consumed or elements_consumed):
                try:
                    result.append(sedes.deserialize(element))
                except DeserializationError as e:
                    raise ListDeserializationError(serial=serial, element_exception=e, index=index)
            else:
                if self.strict and not (sedes_consumed and elements_consumed):
                    raise ListDeserializationError('List has wrong length', serial)
                break
        return tuple(result)


class CountableList(object):

    """A sedes for lists of arbitrary length.

    :param element_sedes: when (de-)serializing a list, this sedes will be
                          applied to all of its elements
    :param max_length: maximum number of allowed elements, or `None` for no limit
    """

    def __init__(self, element_sedes, max_length=None):
        self.element_sedes = element_sedes
        self.max_length = max_length

    def serialize(self, obj):
        if not is_sequence(obj):
            raise ListSerializationError('Can only serialize sequences', obj)
        result = []
        for index, element in enumerate(obj):
            try:
                result.append(self.element_sedes.serialize(element))
            except SerializationError as e:
                raise ListSerializationError(obj=obj, element_exception=e, index=index)
        if self.max_length is not None and len(result) > self.max_length:
            raise ListSerializationError('Too many elements ({}, allowed '
                                         '{})'.format(len(result), self.max_length))
        return result

    def deserialize(self, serial):
        if not is_sequence(serial):
            raise ListDeserializationError('Can only deserialize sequences', serial)
        result = []
        for index, element in enumerate(serial):
            try:
                result.append(self.element_sedes.deserialize(element))
            except DeserializationError as e:
                raise ListDeserializationError(serial=serial, element_exception=e, index=index)
            if self.max_length is not None and index >= self.max_length:
                raise ListDeserializationError('Too many elements (more than '
                                               '{})'.format(self.max_length), serial)
        return tuple(result)


class Serializable(object):

    """Base class for objects which can be serialized into RLP lists.

    :attr:`fields` defines which attributes are serialized and how this is
    done. It is expected to be an ordered sequence of 2-tuples
    ``(name, sedes)``. Here, ``name`` is the name of an attribute and ``sedes``
    is the sedes object that will be used to serialize the corresponding
    attribute. The object as a whole is then serialized as a list of those
    fields.

    :cvar fields: a list of 2-tuples ``(name, sedes)`` where ``name`` is a
                  string corresponding to an attribute and ``sedes`` is the
                  sedes object used for (de)serializing the attribute.
    :param \*args: initial values for the first attributes defined via
                  :attr:`fields`
    :param \*\*kwargs: initial values for all attributes not initialized via
                       positional arguments
    :ivar _cached_rlp: can be used to store the object's RLP code (by default
                       `None`)
    :ivar _mutable: if `False`, all attempts to set field values will fail (by
                    default `True`, unless created with :meth:`deserialize`)
    """

    fields = tuple()
    _sedes = None
    _mutable = True
    _cached_rlp = None

    def __init__(self, *args, **kwargs):

        # check keyword arguments are known
        field_set = set(field for field, _ in self.fields)

        # set positional arguments
        for (field, _), arg in zip(self.fields, args):
            setattr(self, field, arg)
            field_set.remove(field)

        # set keyword arguments, if not already set
        for (field, value) in kwargs.items():
            if field in field_set:
                setattr(self, field, value)
                field_set.remove(field)

        if len(field_set) != 0:
            raise TypeError('Not all fields initialized')

    def __setattr__(self, attr, value):
        try:
            mutable = self.is_mutable()
        except AttributeError:
            mutable = True
            self.__dict__['_mutable'] = True  # don't call __setattr__ again
        if mutable or attr not in set(field for field, _ in self.fields):
            super(Serializable, self).__setattr__(attr, value)
        else:
            raise ValueError('Tried to mutate immutable object')

    def __eq__(self, other):
        """Two objects are equal, if they are equal after serialization."""
        if not hasattr(other.__class__, 'serialize'):
            return False
        return self.serialize(self) == other.serialize(other)

    def __ne__(self, other):
        return not self == other

    def is_mutable(self):
        """Checks if the object is mutable"""
        return self._mutable

    def make_immutable(self):
        """Make it immutable to prevent accidental changes.

        `obj.make_immutable` is equivalent to `make_immutable(obj)`, but doesn't return
        anything.
        """
        make_immutable(self)

    @classmethod
    def get_sedes(cls):
        if not cls._sedes:
            cls._sedes = List(sedes for _, sedes in cls.fields)
        return cls._sedes

    @classmethod
    def serialize(cls, obj):
        if not hasattr(obj, 'fields'):
            raise ObjectSerializationError('Cannot serialize this object (no fields)', obj)
        try:
            field_values = [getattr(obj, field) for field, _ in cls.fields]
        except AttributeError:
            raise ObjectSerializationError('Cannot serialize this object (missing attribute)', obj)
        try:
            result = cls.get_sedes().serialize(field_values)
        except ListSerializationError as e:
            raise ObjectSerializationError(obj=obj, sedes=cls, list_exception=e)
        else:
            return result

    @classmethod
    def deserialize(cls, serial, exclude=None, **kwargs):
        try:
            values = cls.get_sedes().deserialize(serial)
        except ListDeserializationError as e:
            raise ObjectDeserializationError(serial=serial, sedes=cls, list_exception=e)
        params = {field: value for (field, _), value
                  in zip(cls.fields, values)}
        if exclude:
            for k in exclude:
                del params[k]
        obj = cls(**dict(list(params.items()) + list(kwargs.items())))
        obj._mutable = False
        return obj

    @classmethod
    def exclude(cls, excluded_fields):
        """Create a new sedes considering only a reduced set of fields."""
        class SerializableExcluded(cls):
            fields = [(field, sedes) for field, sedes in cls.fields
                      if field not in excluded_fields]
            _sedes = None
        return SerializableExcluded


def make_immutable(x):
    """Do your best to make `x` as immutable as possible.

    If `x` is a sequence, apply this function recursively to all elements and return a tuple
    containing them. If `x` is an instance of :class:`rlp.Serializable`, apply this function to its
    fields, and set :attr:`_mutable` to `False`. If `x` is neither of the above, just return `x`.

    :returns: `x` after making it immutable
    """
    if isinstance(x, Serializable):
        x._mutable = True
        for field, _ in x.fields:
            attr = getattr(x, field)
            try:
                setattr(x, field, make_immutable(attr))
            except AttributeError:
                pass  # respect read only properties
        x._mutable = False
        return x
    elif is_sequence(x):
        return tuple(make_immutable(element) for element in x)
    else:
        return x
