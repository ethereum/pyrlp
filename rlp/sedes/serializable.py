import abc
import collections

from eth_utils import (
    to_tuple,
    to_dict,
)

from rlp.exceptions import (
    ListSerializationError,
    ObjectSerializationError,
    ListDeserializationError,
    ObjectDeserializationError,
)

from .lists import (
    List,
)


class MetaBase:
    fields = None
    field_names = None
    field_attrs = None
    sedes = None


def validate_args_and_kwargs(args, kwargs, arg_names):
    if len(arg_names) != len(set(arg_names)):
        raise TypeError("duplicate argument names")

    needed_kwargs = arg_names[len(args):]
    used_kwargs = set(arg_names[:len(args)])

    duplicate_kwargs = used_kwargs.intersection(kwargs.keys())
    if duplicate_kwargs:
        raise TypeError("Duplicate kwargs: {0}".format(sorted(duplicate_kwargs)))

    unknown_kwargs = set(kwargs.keys()).difference(arg_names)
    if unknown_kwargs:
        raise TypeError("Unknown kwargs: {0}".format(sorted(unknown_kwargs)))

    missing_kwargs = set(needed_kwargs).difference(kwargs.keys())
    if missing_kwargs:
        raise TypeError("Missing kwargs: {0}".format(sorted(missing_kwargs)))


@to_tuple
def merge_kwargs_to_args(args, kwargs, arg_names):
    validate_args_and_kwargs(args, kwargs, arg_names)

    needed_kwargs = arg_names[len(args):]

    yield from args
    for arg_name in needed_kwargs:
        yield kwargs[arg_name]


@to_dict
def merge_args_to_kwargs(args, kwargs, arg_names):
    validate_args_and_kwargs(args, kwargs, arg_names)

    yield from kwargs.items()
    for value, name in zip(args, arg_names):
        yield name, value


def _eq(left, right):
    """
    Equality comparison that allows for equality between tuple and list types
    with equivalent elements.
    """
    if isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
        return len(left) == len(right) and all(_eq(*pair) for pair in zip(left, right))
    else:
        return left == right


class BaseSerializable(collections.Sequence):
    def __init__(self, *args, **kwargs):
        if kwargs:
            field_values = merge_kwargs_to_args(args, kwargs, self._meta.field_names)
        else:
            field_values = args

        if len(field_values) != len(self._meta.field_names):
            raise TypeError(
                'Argument count mismatch. expected {0} - got {1} - missing {2}'.format(
                    len(self._meta.field_names),
                    len(field_values),
                    ','.join(self._meta.field_names[len(field_values):]),
                )
            )

        for value, attr in zip(field_values, self._meta.field_attrs):
            setattr(self, attr, value)

    _is_mutable = None

    @property
    def is_mutable(self):
        return bool(self._is_mutable)

    @property
    def is_immutable(self):
        return not self.is_mutable

    @classmethod
    def create_mutable(cls, *args, **kwargs):
        obj = cls(*args, **kwargs)
        obj._is_mutable = True
        return obj

    @classmethod
    def create_immutable(cls, *args, **kwargs):
        obj = cls(*args, **kwargs)
        obj._is_mutable = False
        return obj

    def as_mutable(self):
        kwargs = {field: make_mutable(value) for field, value in self.as_dict().items()}
        return type(self).create_mutable(**kwargs)

    def as_immutable(self):
        kwargs = {field: make_immutable(value) for field, value in self.as_dict().items()}
        return type(self).create_immutable(**kwargs)

    _cached_rlp = None

    def as_dict(self):
        return dict(
            (field, value)
            for field, value
            in zip(self._meta.field_names, self)
        )

    def __iter__(self):
        for attr in self._meta.field_attrs:
            yield getattr(self, attr)

    def __getitem__(self, idx):
        if isinstance(idx, int):
            attr = self._meta.field_attrs[idx]
            return getattr(self, attr)
        elif isinstance(idx, slice):
            field_slice = self._meta.field_Gttrs[idx]
            return tuple(getattr(self, field) for field in field_slice)
        elif isinstance(idx, str):
            return getattr(self, idx)
        else:
            raise IndexError("Unsupported type for __getitem__: {0}".format(type(idx)))

    def __len__(self):
        return len(self._meta.fields)

    def __eq__(self, other):
        return isinstance(other, Serializable) and hash(self) == hash(other)

    _hash_cache = None

    def __hash__(self):
        if self.is_mutable:
            return hash(tuple(make_immutable(value) for value in self))
        elif self._hash_cache is None:
            self._hash_cache = hash(tuple(make_immutable(value) for value in self))

        return self._hash_cache

    @classmethod
    def serialize(cls, obj):
        try:
            return cls._meta.sedes.serialize(obj)
        except ListSerializationError as e:
            raise ObjectSerializationError(obj=obj, sedes=cls, list_exception=e)

    @classmethod
    def deserialize(cls, serial, mutable=False, **kwargs):
        try:
            values = cls._meta.sedes.deserialize(serial)
        except ListDeserializationError as e:
            raise ObjectDeserializationError(serial=serial, sedes=cls, list_exception=e)

        if mutable:
            value_kwargs = merge_args_to_kwargs(values, {}, cls._meta.field_names)
            return cls.create_mutable(**value_kwargs, **kwargs)
        else:
            immutable_args = tuple(make_immutable(arg) for arg in values)
            value_kwargs = merge_args_to_kwargs(immutable_args, {}, cls._meta.field_names)
            return cls.create_immutable(**value_kwargs, **kwargs)


def make_immutable(value):
    if hasattr(value, 'as_immutable'):
        return value.as_immutable()
    elif not isinstance(value, (bytes, str)) and isinstance(value, collections.Sequence):
        return tuple(make_immutable(item) for item in value)
    else:
        return value


def make_mutable(value):
    if hasattr(value, 'as_mutable'):
        return value.as_mutable()
    elif not isinstance(value, (bytes, str)) and isinstance(value, collections.Sequence):
        return list(make_mutable(item) for item in value)
    else:
        return value


@to_tuple
def _mk_field_attrs(field_names, extra_namespace):
    namespace = set(field_names).union(extra_namespace)
    for field in field_names:
        while True:
            field = '_' + field
            if field not in namespace:
                namespace.add(field)
                yield field
                break


def _mk_field_property(field, attr):
    @property
    def field_fn(self):
        return getattr(self, attr)

    @field_fn.setter
    def field_fn(self, value):
        if self.is_mutable:
            setattr(self, attr, value)
            self._cached_rlp = None
        else:
            raise AttributeError("can't set attribute")

    return field_fn


class SerializableBase(abc.ABCMeta):
    def __new__(cls, name, bases, attrs):
        super_new = super(SerializableBase, cls).__new__

        # Ensure initialization is only performed for subclasses of SerializableBase
        # (excluding Model class itself).
        is_serializable_subclass = any(b for b in bases if isinstance(b, SerializableBase))
        declares_fields = 'fields' in attrs

        if not is_serializable_subclass or not declares_fields:
            return super_new(cls, name, bases, attrs)

        fields = attrs.pop('fields')
        field_names, sedes = zip(*fields)

        field_attrs = _mk_field_attrs(field_names, attrs.keys())

        meta_namespace = {
            'fields': fields,
            'field_attrs': field_attrs,
            'field_names': field_names,
            'sedes': List(sedes),
        }

        meta_base = attrs.pop('_meta', MetaBase)
        meta = type(
            'Meta',
            (meta_base,),
            meta_namespace,
        )
        attrs['_meta'] = meta

        field_props = {
            field: _mk_field_property(field, attr)
            for field, attr
            in zip(meta.field_names, meta.field_attrs)
        }

        return super_new(
            cls,
            name,
            bases,
            dict(
                tuple(field_props.items()) +
                tuple(attrs.items()) +
                (('__slots__', meta.field_attrs),)
            ),
        )


class Serializable(BaseSerializable, metaclass=SerializableBase):
    pass
