import collections
import sys
from .exceptions import EncodingError, DecodingError
from .utils import (Atomic, str_to_bytes, is_integer, bytes_to_int_array,
                    ascii_chr)
from .sedes.binary import Binary as BinaryClass
from .sedes import big_endian_int, binary
from .sedes.lists import List, is_sedes


if sys.version_info.major == 2:
    from itertools import imap as map


def encode(obj, sedes=None, infer_serializer=True):
    """Encode a Python object in RLP format.

    By default, the object is serialized in a suitable way first (using
    :func:`rlp.infer_sedes`) and then encoded. Serialization can be
    explicitly suppressed by setting `infer_serializer` to ``False`` and not
    passing an alternative as `sedes`.

    :param sedes: an object implementing a function ``serialize(obj)`` which
                  will be used to serialize ``obj`` before encoding, or
                  ``None`` to use the infered one (if any)
    :param infer_serializer: if ``True`` an appropriate serializer will be
                             selected using :func:`rlp.infer_sedes` to
                             serialize `obj` before encoding
    :returns: the RLP encoded item
    :raises: :exc:`rlp.EncodingError` in the rather unlikely case that the item
             is too big to encode (will not happen)
    :raises: :exc:`rlp.SerializationError` if the serialization fails
    """
    if sedes:
        item = sedes.serialize(obj)
    elif infer_serializer:
        item = infer_sedes(obj).serialize(obj)
    else:
        item = obj
    return encode_raw(item)


def encode_raw(item):
    """RLP encode (a nested sequence of) :class:`Atomic`s."""
    if isinstance(item, Atomic):
        if len(item) == 1 and bytes_to_int_array(item)[0] < 128:
            return str_to_bytes(item)
        payload = str_to_bytes(item)
        prefix_offset = 128  # string
    elif isinstance(item, collections.Sequence):
        payload = b''.join(map(encode_raw, item))
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
        length_string = big_endian_int.serialize(length)
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
    if isinstance(rlp, str):
        rlp = str_to_bytes(rlp)

    b0 = bytes_to_int_array(rlp)[start]
    if b0 < 128:  # single byte
        return (str, 1, start)
    elif b0 < 128 + 56:  # short string
        return (str, b0 - 128, start + 1)
    elif b0 < 192:  # long string
        ll = b0 - 128 - 56 + 1
        l = big_endian_int.deserialize(rlp[start + 1:start + 1 + ll])
        return (str, l, start + 1 + ll)
    elif b0 < 192 + 56:  # short list
        return (list, b0 - 192, start + 1)
    else:  # long list
        ll = b0 - 192 - 56 + 1
        l = big_endian_int.deserialize(rlp[start + 1:start + 1 + ll])
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
            item, next_item_start = consume_item(rlp, next_item_start)
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

    :param sedes: an object implementing a function ``deserialize(code)`` which
                  will be applied after decoding, or ``None`` if no
                  deserialization should be performed
    :param \*\*kwargs: additional keyword arguments that will be passed to the
                     deserializer
    :param strict: if false inputs that are longer than necessary don't cause
                   an exception
    :returns: the decoded and maybe deserialized Python object
    :raises: :exc:`rlp.DecodingError` if the input string does not end after
             the root item and `strict` is true
    :raises: :exc:`rlp.DeserializationError` if the deserialization fails
    """
    try:
        item, end = consume_item(rlp, 0)
    except IndexError:
        raise DecodingError('RLP string to short', rlp)
    if end != len(rlp) and strict:
        msg = 'RLP string ends with {} superfluous bytes'.format(len(rlp) - end)
        raise DecodingError(msg, rlp)
    if sedes:
        return sedes.deserialize(item, **kwargs)
    else:
        return item


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
