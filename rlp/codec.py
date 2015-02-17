import abc
import collections
from functools import partial
from itertools import izip, imap
from .exceptions import EncodingError, DecodingError
from .utils import Atomic
from .sedes import big_endian_int, sedes_list
from .sedes.inference import infer_sedes


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
        item = infer_sedes(obj, sedes_list).serialize(obj)
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


def consume_item(rlp, start=0):
    """Read an item from an RLP string.
    
    :param rlp: the rlp string to read from
    :param start: the position at which to start reading
    :returns: a tuple ``(item, end)``, where ``item`` is the read item and
              ``end`` is the position of the first unprocessed byte
    """
    b0 = ord(rlp[start])
    if b0 < 128:  # single byte
        return (rlp[start], start + 1)
    elif b0 < 128 + 56:
        l = b0 - 128  # short string
        return (rlp[start + 1:start + 1 + l], start + 1 + l)
    elif b0 < 192:  # long string
        ll = b0 - 128 - 56 + 1
        l = big_endian_int.deserialize(rlp[start + 1:start + 1 + ll])
        return (rlp[start + 1 + ll:start + 1 + ll + l], start + 1 + l + ll)
    elif b0 < 192 + 56:  # short list
        end = start + 1 + b0 - 192
        items = []
        next_item_start = start + 1
        while next_item_start < end:
            item, next_item_start = consume_item(rlp, next_item_start)
            items.append(item)
        if next_item_start > end:
            raise DecodingError('List length prefix announced a too small '
                                'length', rlp)
        return (items, next_item_start)
    else: # long list
        ll = b0 - 192 - 56 + 1
        l = big_endian_int.deserialize(rlp[start + 1:start + 1 + ll])
        if l < 56:
            raise DecodingError('Long list prefix used for short list', rlp)
        items = []
        next_item_start = start + 1 + ll
        end = next_item_start + l
        while next_item_start < end:
            item, next_item_start = consume_item(rlp, next_item_start)
            items.append(item)
        if next_item_start > end:
            raise DecodingError('List length prefix announced a too small '
                                'length', rlp)
        return (items, next_item_start)


def decode(rlp, sedes=None):
    """Decode an RLP encoded object.

    :param sedes: an object implementing a function ``deserialize(code)`` which
                  will be applied after decoding, or ``None`` if no
                  deserialization should be performed
    :returns: the decoded and maybe deserialized Python object
    :raises: :exc:`DecodingError` if the input string does not end after the
             root item
    """
    try:
        item, end = consume_item(rlp)
    except IndexError:
        raise DecodingError('RLP string to short', rlp)
    if end != len(rlp):
        print end, len(rlp)
        msg = 'RLP string ends with {} superfluous bytes'.format(len(rlp) - end)
        raise DecodingError(msg, rlp)
    if sedes:
        return sedes.deserialize(item)
    else:
        return item
