import abc
import collections
from functools import partial
from itertools import izip, imap
from .sedes import big_endian_int, sedes_list
from .exceptions import EncodingError, DecodingError
from .utils import infer_sedes


class Atomic(object):
    """ABC for objects that can be RLP encoded as is."""
    __metaclass__ = abc.ABCMeta


Atomic.register(str)
Atomic.register(bytearray)


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


def consume_length_prefix(rlp):
    """Read the length prefix of from the beginning of an RLP string.

    This returns a 3-tuple with the following entries:

    ``type``
        either ``str`` or ``list`` depending on the type of the encoded item

    ``length``
        the length of the encoded data in bytes

    ``tail``
        the unprocessed rest of the input string (starting with an unprefixed
        payload)
    
    :returns: a tuple ``(type, length, tail)`` as described above
    :raises: :exc:`DecodingError` if the length prefix is invalid (the payload
             is not further checked, however)
    """
    b0 = ord(rlp[0])
    branch = {
               0 <= b0 < 128:      'single_byte',
             128 <= b0 < 128 + 56: 'short_string',
        128 + 56 <= b0 < 192:      'long_string',
             192 <= b0 < 192 + 56: 'short_list',
        192 + 56 <= b0 < 256:      'long_list'
    }[True]

    if branch == 'single_byte':
        return (str, 1, rlp)
    elif branch == 'short_string':
        return (str, b0 - 128, rlp[1:])
    elif branch == 'short_list':
        return (list, b0 - 192, rlp[1:])
    else:
        length_length = b0 - 56 + 1
        if branch == 'long_string':
            type_ = str
            length_length -= 128
        elif branch == 'long_list':
            type_ = list
            length_length -= 192
        else:
            assert False, 'Unreachable'
        length_encoded = rlp[1:1 + length_length]
        try:
            length = big_endian_int.deserialize(length_encoded)
        except DeserializationError:
            raise DecodingError('Invalid length prefix encountered', rlp)
        return (type_, length, rlp[1 + length_length:])


def consume_item(rlp):
    """Read and decode an item from the beginning of an RLP string.
    
    This returns a 2-tuple with the following entries:

    ``item``
        the decoded item

    ``tail``
        the unprocessed rest of the input string

    :param rlp: the RLP string, beginning with a length prefix
    :returns: a tuple ``(item, tail)`` as described above
    :raises: :exc:`DecodingError` if the length of the payload is shorter than
             claimed by its length prefix
    """
    type_, length, residual = consume_length_prefix(rlp)
    payload = residual[:length]
    tail = residual[length:]
    if len(payload) != length:
        msg = ('Payload too short (clipped after {} bytes, but length prefix '
               'announced {})'.format(len(payload), length))
        raise DecodingError(msg, rlp)

    if type_ == str:
        return (str(payload), tail)
    else:
        elements = []
        while payload:
            item, payload = consume_item(payload)
            elements.append(item)
        return (elements, tail)


def decode(rlp, sedes=None):
    """Decode an RLP encoded object.

    :param sedes: an object implementing a function ``deserialize(code)`` which
                  will be applied after decoding, or ``None`` if no
                  deserialization should be performed
    :returns: the decoded and maybe deserialized Python object
    :raises: :exc:`DecodingError` if the input string does not end after the
             root item
    """
    item, tail = consume_item(rlp)
    if tail:
        msg = 'RLP string ends with {} superfluous bytes'.format(len(tail))
        raise DecodingError(msg, rlp)
    if sedes:
        return sedes.deserialize(item)
    else:
        return item
