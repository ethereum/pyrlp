from collections import Sequence
import pytest
import rlp


def evaluate(lazy_list):
    if isinstance(lazy_list, rlp.lazy.LazyList):
        return [evaluate(e) for e in lazy_list]
    else:
        return lazy_list


def test_empty_list():
    dec = lambda: rlp.decode_lazy(rlp.encode([]))
    assert isinstance(dec(), Sequence) 
    with pytest.raises(IndexError):
        dec()[0]
    with pytest.raises(IndexError):
        dec()[1]
    assert len(dec()) == 0
    assert evaluate(dec()) == []


def test_string():
    for s in ('', 'asdf', 'a' * 56, 'b' * 123):
        dec = lambda: rlp.decode_lazy(rlp.encode(s))
        assert isinstance(dec(), str)
        assert len(dec()) == len(s)
        assert dec() == s


def test_nested_list():
    l = [[], ['a'], ['b', 'c', 'd']]
    dec = lambda: rlp.decode_lazy(rlp.encode(l))
    assert isinstance(dec(), Sequence)
    assert len(dec()) == len(l)
    assert evaluate(dec()) == l
    with pytest.raises(IndexError):
        assert dec()[0][0]
    with pytest.raises(IndexError):
        assert dec()[1][1]
    with pytest.raises(IndexError):
        assert dec()[2][3]
    with pytest.raises(IndexError):
        assert dec()[3]
