import collections
import sys

from rlp.exceptions import EncodingError, DecodingError
from rlp.utils import (
    Atomic,
    ascii_chr,
    big_endian_to_int,
    decode_hex,
    encode_hex,
    int_to_big_endian,
    is_integer,
    safe_ord,
    str_to_bytes,
)
from rlp.sedes.binary import Binary as BinaryClass
from rlp.sedes import big_endian_int, binary
from rlp.sedes.lists import List, Serializable, is_sedes


def encode(obj, sedes=None, infer_serializer=True, cache=False):
    """Encode a Python object in RLP format.

    By default, the object is serialized in a suitable way first (using :func:`rlp.infer_sedes`)
    and then encoded. Serialization can be explicitly suppressed by setting `infer_serializer` to
    ``False`` and not passing an alternative as `sedes`.

    If `obj` has an attribute :attr:`_cached_rlp` (as, notably, :class:`rlp.Serializable`) and its
    value is not `None`, this value is returned bypassing serialization and encoding, unless
    `sedes` is given (as the cache is assumed to refer to the standard serialization which can be
    replaced by specifying `sedes`).

    If `obj` is a :class:`rlp.Serializable` and `cache` is true, the result of the encoding will be
    stored in :attr:`_cached_rlp` if it is empty and :meth:`rlp.Serializable.make_immutable` will
    be invoked on `obj`.

    :param sedes: an object implementing a function ``serialize(obj)`` which will be used to
                  serialize ``obj`` before encoding, or ``None`` to use the infered one (if any)
    :param infer_serializer: if ``True`` an appropriate serializer will be selected using
                             :func:`rlp.infer_sedes` to serialize `obj` before encoding
    :param cache: cache the return value in `obj._cached_rlp` if possible and make `obj` immutable
                  (default `False`)
    :returns: the RLP encoded item
    :raises: :exc:`rlp.EncodingError` in the rather unlikely case that the item is too big to
             encode (will not happen)
    :raises: :exc:`rlp.SerializationError` if the serialization fails
    """
    if isinstance(obj, Serializable):
        if obj._cached_rlp and sedes is None:
            return obj._cached_rlp
        else:
            really_cache = cache if sedes is None else False
    else:
        really_cache = False

    if sedes:
        item = sedes.serialize(obj)
    elif infer_serializer:
        item = infer_sedes(obj).serialize(obj)
    else:
        item = obj

    result = encode_raw(item)
    if really_cache:
        obj._cached_rlp = result
        obj.make_immutable()
    return result


def hex_encode(obj, sedes=None, infer_serializer=True, cache=False,
               prefixed=False):
    return ('0x' * prefixed) + \
        encode_hex(encode(obj, sedes, infer_serializer, cache))

def prefix_hex_encode(obj, sedes=None, infer_serializer=True, cache=False):
    return '0x'+encode_hex(encode(obj, sedes, infer_serializer, cache))


class RLPData(str):

    "wraper to mark already rlp serialized data"
    pass


def encode_raw(item):
    """RLP encode (a nested sequence of) :class:`Atomic`s."""
    if isinstance(item, RLPData):
        return item
    elif isinstance(item, Atomic):
        if len(item) == 1 and safe_ord(item[0]) < 128:
            return str_to_bytes(item)
        payload = str_to_bytes(item)
        prefix_offset = 128  # string
    elif isinstance(item, collections.Sequence):
        payload = b''.join(encode_raw(x) for x in item)
        prefix_offset = 192  # list
    else:
        msg = 'Cannot encode object of type {0}'.format(type(item).__name__)
        raise EncodingError(msg, item)

    try:
        prefix = length_prefix(len(payload), prefix_offset)
    except ValueError:
        raise EncodingError('Item too big to encode', item)

    return prefix + payload


def length_prefix(length, offset):
    """Construct the prefix to lists or strings denoting their length.

    :param length: the length of the item in bytes
    :param offset: ``0x80`` when encoding raw bytes, ``0xc0`` when encoding a
                   list
    """
    if length < 56:
        return ascii_chr(offset + length)
    elif length < 256**8:
        length_string = int_to_big_endian(length)
        return ascii_chr(offset + 56 - 1 + len(length_string)) + length_string
    else:
        raise ValueError('Length greater than 256**8')


def consume_length_prefix(rlp, start):
    """Read a length prefix from an RLP string.

    :param rlp: the rlp string to read from
    :param start: the position at which to start reading
    :returns: a tuple ``(type, length, end)``, where ``type`` is either ``str``
              or ``list`` depending on the type of the following payload,
              ``length`` is the length of the payload in bytes, and ``end`` is
              the position of the first payload byte in the rlp string
    """
    b0 = safe_ord(rlp[start])
    if b0 < 128:  # single byte
        return (str, 1, start)
    elif b0 < 128 + 56:  # short string
        if b0 - 128 == 1 and safe_ord(rlp[start + 1]) < 128:
            raise DecodingError('Encoded as short string although single byte was possible', rlp)
        return (str, b0 - 128, start + 1)
    elif b0 < 192:  # long string
        ll = b0 - 128 - 56 + 1
        if rlp[start + 1:start + 2] == b'\x00':
            raise DecodingError('Length starts with zero bytes', rlp)
        l = big_endian_to_int(rlp[start + 1:start + 1 + ll])
        if l < 56:
            raise DecodingError('Long string prefix used for short string', rlp)
        return (str, l, start + 1 + ll)
    elif b0 < 192 + 56:  # short list
        return (list, b0 - 192, start + 1)
    else:  # long list
        ll = b0 - 192 - 56 + 1
        if rlp[start + 1:start + 2] == b'\x00':
            raise DecodingError('Length starts with zero bytes', rlp)
        l = big_endian_to_int(rlp[start + 1:start + 1 + ll])
        if l < 56:
            raise DecodingError('Long list prefix used for short list', rlp)
        return (list, l, start + 1 + ll)


def consume_payload(rlp, start, type_, length):
    """Read the payload of an item from an RLP string.

    :param rlp: the rlp string to read from
    :param type_: the type of the payload (``str`` or ``list``)
    :param start: the position at which to start reading
    :param length: the length of the payload in bytes
    :returns: a tuple ``(item, end)``, where ``item`` is the read item and
              ``end`` is the position of the first unprocessed byte
    """
    if type_ == str:
        return (rlp[start:start + length], start + length)
    elif type_ == list:
        items = []
        next_item_start = start
        end = next_item_start + length
        while next_item_start < end:
            # item, next_item_start = consume_item(rlp, next_item_start)
            t, l, s = consume_length_prefix(rlp, next_item_start)
            item, next_item_start = consume_payload(rlp, s, t, l)
            items.append(item)
        if next_item_start > end:
            raise DecodingError('List length prefix announced a too small '
                                'length', rlp)
        return (items, next_item_start)
    else:
        raise TypeError('Type must be either list or str')


def consume_item(rlp, start):
    """Read an item from an RLP string.

    :param rlp: the rlp string to read from
    :param start: the position at which to start reading
    :returns: a tuple ``(item, end)`` where ``item`` is the read item and
              ``end`` is the position of the first unprocessed byte
    """
    t, l, s = consume_length_prefix(rlp, start)
    return consume_payload(rlp, s, t, l)


def decode(rlp, sedes=None, strict=True, **kwargs):
    """Decode an RLP encoded object.

    If the deserialized result `obj` has an attribute :attr:`_cached_rlp` (e.g. if `sedes` is a
    subclass of :class:`rlp.Serializable`) it will be set to `rlp`, which will improve performance
    on subsequent :func:`rlp.encode` calls. Bear in mind however that `obj` needs to make sure that
    this value is updated whenever one of its fields changes or prevent such changes entirely
    (:class:`rlp.sedes.Serializable` does the latter).

    :param sedes: an object implementing a function ``deserialize(code)`` which will be applied
                  after decoding, or ``None`` if no deserialization should be performed
    :param \*\*kwargs: additional keyword arguments that will be passed to the deserializer
    :param strict: if false inputs that are longer than necessary don't cause an exception
    :returns: the decoded and maybe deserialized Python object
    :raises: :exc:`rlp.DecodingError` if the input string does not end after the root item and
             `strict` is true
    :raises: :exc:`rlp.DeserializationError` if the deserialization fails
    """
    rlp = str_to_bytes(rlp)
    try:
        item, end = consume_item(rlp, 0)
    except IndexError:
        raise DecodingError('RLP string to short', rlp)
    if end != len(rlp) and strict:
        msg = 'RLP string ends with {} superfluous bytes'.format(len(rlp) - end)
        raise DecodingError(msg, rlp)
    if sedes:
        obj = sedes.deserialize(item, **kwargs)
        if hasattr(obj, '_cached_rlp'):
            obj._cached_rlp = rlp
            assert not isinstance(obj, Serializable) or not obj.is_mutable()
        return obj
    else:
        return item

def hex_decode(rlp, sedes=None, strict=True, **kwargs):
    return decode(decode_hex(rlp[2:] if rlp[:2] == '0x' else rlp),
                  sedes, strict, **kwargs)

def descend(rlp, *path):
    rlp = str_to_bytes(rlp)
    for p in path:
        pos = 0
        _typ, _len, pos = consume_length_prefix(rlp, pos)
        if _typ != list:
            raise DecodingError('Trying to descend through a non-list!', rlp)
        for i in range(p):
            _, _l, _p = consume_length_prefix(rlp, pos)
            pos = _l + _p
        _, _l, _p = consume_length_prefix(rlp, pos)
        rlp = rlp[pos: _p + _l]
    return rlp

def infer_sedes(obj):
    """Try to find a sedes objects suitable for a given Python object.

    The sedes objects considered are `obj`'s class, `big_endian_int` and
    `binary`. If `obj` is a sequence, a :class:`rlp.sedes.List` will be
    constructed recursively.

    :param obj: the python object for which to find a sedes object
    :raises: :exc:`TypeError` if no appropriate sedes could be found
    """
    if is_sedes(obj.__class__):
        return obj.__class__
    if is_integer(obj) and obj >= 0:
        return big_endian_int
    if BinaryClass.is_valid_type(obj):
        return binary
    if isinstance(obj, collections.Sequence):
        return List(map(infer_sedes, obj))
    msg = 'Did not find sedes handling type {}'.format(type(obj).__name__)
    raise TypeError(msg)

def append(rlpdata, obj):
    _typ, _len, _pos = consume_length_prefix(rlpdata, 0)
    assert _typ is list
    rlpdata = rlpdata[_pos:] + encode(obj)
    prefix = length_prefix(len(rlpdata), 192)
    return prefix + rlpdata

def insert(rlpdata, index, obj):
    _typ, _len, _pos = consume_length_prefix(rlpdata, 0)
    _beginpos = _pos
    assert _typ is list
    for i in range(index):
        _, _l, _p = consume_length_prefix(rlpdata, _pos)
        _pos = _l + _p
        if _l + _p >= len(rlpdata):
            break
    rlpdata = rlpdata[_beginpos:_pos] + encode(obj) + rlpdata[_pos:]
    prefix = length_prefix(len(rlpdata), 192)
    return prefix + rlpdata

def pop(rlpdata, index=2**50):
    _typ, _len, _pos = consume_length_prefix(rlpdata, 0)
    _initpos = _pos
    assert _typ is list
    while index > 0:
        _, _l, _p = consume_length_prefix(rlpdata, _pos)
        if _l + _p >= len(rlpdata):
            break
        _pos = _l + _p
        index -= 1
    _, _l, _p = consume_length_prefix(rlpdata, _pos)
    newdata = rlpdata[_initpos:_pos] + rlpdata[_l + _p:]
    prefix = length_prefix(len(newdata), 192)
    return prefix + newdata

EMPTYLIST = encode([])

def compare_length(rlpdata, length):
    _typ, _len, _pos = consume_length_prefix(rlpdata, 0)
    _initpos = _pos
    assert _typ is list
    lenlist = 0
    if rlpdata == EMPTYLIST:
        return -1 if length > 0 else 1 if length < 0 else 0
    while 1:
        if lenlist > length:
            return 1
        _, _l, _p = consume_length_prefix(rlpdata, _pos)
        lenlist += 1
        if _l + _p >= len(rlpdata):
            break
        _pos = _l + _p
    return 0 if lenlist == length else -1
