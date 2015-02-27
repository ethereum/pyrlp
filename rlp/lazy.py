from collections import Sequence
from .exceptions import DecodingError
from .codec import consume_length_prefix, consume_payload


def decode_lazy(rlp):
    item, end = consume_item_lazy(rlp, 0)
    if end != len(rlp):
        raise DecodingError('RLP length prefix announced wrong length')
    return item


def consume_item_lazy(rlp, start):
    t, l, s = consume_length_prefix(rlp, start)
    if t == str:
        item, _ = consume_payload(rlp, s, str, l), s + l
        return item
    else:
        assert t == list
        return LazyList(rlp, s), s + l


class LazyList(Sequence):

    def __init__(self, rlp, start):
        self.rlp = rlp
        self.start = start
        self.index = start
        self.elements_ = []
        self.len_ = None

    def next(self):
        try:
            item, end = consume_item_lazy(self.rlp, self.index)
        except IndexError:
            raise StopIteration
        self.index = end
        self.elements_.append(item)
        return item

    def __getitem__(self, i):
        try:
            while len(self.elements_) <= i:
                next(self)
        except StopIteration:
            self.len_ = len(self.elements_)
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
