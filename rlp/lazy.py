from collections import Sequence
from .exceptions import DecodingError, DeserializationError
from .codec import consume_length_prefix, consume_payload


def decode_lazy(rlp, sedes=None, **kwargs):
    item, end = consume_item_lazy(rlp, 0)
    if end != len(rlp):
        raise DecodingError('RLP length prefix announced wrong length', rlp)
    if isinstance(item, LazyList):
        item.sedes = sedes
        return item
    elif sedes:
        return sedes.deserialize(item)
    else:
        return item

def consume_item_lazy(rlp, start):
    t, l, s = consume_length_prefix(rlp, start)
    if t == str:
        #item, _ = consume_payload(rlp, s, str, l), s + l
        return consume_payload(rlp, s, str, l)
    else:
        assert t == list
        return LazyList(rlp, s, s + l), s + l


class LazyList(Sequence):

    def __init__(self, rlp, start, end, sedes=None):
        self.rlp = rlp
        self.start = start
        self.end = end
        self.index = start
        self.elements_ = []
        self.len_ = None
        self.sedes = sedes

    def next(self):
        if self.index == self.end:
            self.len_ = len(self.elements_)
            raise StopIteration
        assert self.index < self.end
        item, end = consume_item_lazy(self.rlp, self.index)
        self.index = end
        if self.sedes:
            try:
                item = self.sedes[len(self.elements_)].deserialize(item)
            except IndexError:
                raise DeserializationError('List has wrong length', self)
        self.elements_.append(item)
        return item

    def __getitem__(self, i):
        try:
            while len(self.elements_) <= i:
                next(self)
        except StopIteration:
            assert self.index == self.end
            raise IndexError('Index %d out of range' % i)
        return self.elements_[i]

    def __len__(self):
        if not self.len_:
            try:
                while True:
                    next(self)
            except StopIteration:
                self.len_ = len(self.elements_)
        return self.len_
