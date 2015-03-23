from collections import Sequence
from .exceptions import DecodingError, DeserializationError
from .codec import consume_length_prefix, consume_payload


def decode_lazy(rlp, sedes=None, **sedes_kwargs):
    """Decode an RLP encoded object in a lazy fashion.

    If the encoded object is a bytestring, this function acts similar to
    :func:`rlp.decode`. If it is a list however, a :class:`LazyList` is
    returned instead. This object will decode the string lazily, avoiding
    both horizontal and vertical traversing as much as possible.

    The way `sedes` is applied depends on the decoded object: If it is a string
    `sedes` deserializes it as a whole; if it is a list, each element is
    deserialized individually. In both cases, `sedes_kwargs` are passed on.
    Note that, if a deserializer is used, only "horizontal" but not
    "vertical lazyness" can be preserved.
    
    :param rlp: the RLP string to decode
    :param sedes: an object implementing a method ``deserialize(code)``
                          which is used as described above, or ``None`` if no
                          deserialization should be performed
    :param \*\*sedes_kwargs: additional keyword arguments that will be passed
                             to the deserializers
    :returns: either the already decoded and deserialized object (if encoded as
              a string) or an instance of :class:`rlp.LazyList`
    """
    item, end = consume_item_lazy(rlp, 0)
    if end != len(rlp):
        raise DecodingError('RLP length prefix announced wrong length', rlp)
    if isinstance(item, LazyList):
        item.sedes = sedes
        item.sedes_kwargs = sedes_kwargs
        return item
    elif sedes:
        return sedes.deserialize(item, **sedes_kwargs)
    else:
        return item

def consume_item_lazy(rlp, start):
    """Read an item from an RLP string lazily.

    If the length prefix announces a string, the string is read; if it
    announces a list, a :class:`LazyList` is created.
    
    :param rlp: the rlp string to read from
    :param start: the position at which to start reading
    :returns: a tuple ``(item, end)`` where ``item`` is the read string or a
              :class:`LazyList` and ``end`` is the position of the first
              unprocessed byte.
    """
    t, l, s = consume_length_prefix(rlp, start)
    if t == str:
        #item, _ = consume_payload(rlp, s, str, l), s + l
        return consume_payload(rlp, s, str, l)
    else:
        assert t == list
        return LazyList(rlp, s, s + l), s + l


class LazyList(Sequence):
    """A RLP encoded list which decodes itself when necessary.

    Both indexing with positive indices and iterating are supported.
    Getting the length with :func:`len` is possible as well but requires full
    horizontal encoding.

    :param rlp: the rlp string in which the list is encoded
    :param start: the position of the first payload byte of the encoded list
    :param end: the position of the last payload byte of the encoded list
    :param sedes: a sedes object which deserializes each element of the list,
                  or ``None`` for no deserialization
    :param \*\*sedes_kwargs: keyword arguments which will be passed on to the
                             deserializer
    """

    def __init__(self, rlp, start, end, sedes=None, **sedes_kwargs):
        self.rlp = rlp
        self.start = start
        self.end = end
        self.index = start
        self.elements_ = []
        self.len_ = None
        self.sedes = sedes
        self.sedes_kwargs = sedes_kwargs

    def next(self):
        if self.index == self.end:
            self.len_ = len(self.elements_)
            raise StopIteration
        assert self.index < self.end
        item, end = consume_item_lazy(self.rlp, self.index)
        self.index = end
        if self.sedes:
            item = self.sedes.deserialize(item, **self.sedes_kwargs)
        self.elements_.append(item)
        return item

    def __getitem__(self, i):
        try:
            while len(self.elements_) <= i:
                self.next()
        except StopIteration:
            assert self.index == self.end
            raise IndexError('Index %d out of range' % i)
        return self.elements_[i]

    def __len__(self):
        if not self.len_:
            try:
                while True:
                    self.next()
            except StopIteration:
                self.len_ = len(self.elements_)
        return self.len_
