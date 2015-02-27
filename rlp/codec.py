import abc
import collections
from functools import partial
from itertools import izip, imap
from .exceptions import EncodingError, DecodingError
from .utils import Atomic
from .sedes import big_endian_int, binary
from .sedes.lists import List, is_sedes


def encode(obj, sedes=None, infer_serializer=True):
    """Encode a Python object in RLP format.
    
    :param sedes: an object implementing a function ``serialize(obj)`` which
                  will be used to serialize ``obj`` before encoding, or
                  ``None`` if no serialization should be performed
    :param infer_serializer: if ``True``, an appropriate serializer will be
                             selected using :func:`infer_sedes` to serialize
                             ``obj`` before encoding. If ``sedes`` is given,
                             ``infer_serializer`` is ignored.
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
        if len(item) == 1 and ord(item[0]) < 128:
            return str(item)
        payload = str(item)
        prefix_offset = 128  # string
    elif isinstance(item, collections.Sequence):
        payload = ''.join(imap(encode_raw, item))
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
        return chr(offset + length)
    elif length < 256**8:
        length_string = big_endian_int.serialize(length)
        return chr(offset + 56 - 1 + len(length_string)) + length_string
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
    b0 = ord(rlp[start])
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
    else: # long list
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
    item, end = consume_payload(rlp, s, t, l)
    return (item, end)


def decode(rlp, sedes=None, **kwargs):
    """Decode an RLP encoded object.

    :param sedes: an object implementing a function ``deserialize(code)`` which
                  will be applied after decoding, or ``None`` if no
                  deserialization should be performed
    :param **kwargs: additional keyword arguments that will be passed to the
                     deserializer
    :returns: the decoded and maybe deserialized Python object
    :raises: :exc:`DecodingError` if the input string does not end after the
             root item
    """
    try:
        item, end = consume_item(rlp, 0)
    except IndexError:
        raise DecodingError('RLP string to short', rlp)
    if end != len(rlp):
        msg = 'RLP string ends with {} superfluous bytes'.format(len(rlp) - end)
        raise DecodingError(msg, rlp)
    if sedes:
        return sedes.deserialize(item, **kwargs)
    else:
        return item


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
    if isinstance(obj, collections.Sequence):
        return List(imap(infer_sedes, obj))
    msg = 'Did not find sedes handling type {}'.format(type(obj).__name__)
    raise TypeError(msg)
