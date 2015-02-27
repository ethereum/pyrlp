from collections import Sequence
import pytest
import rlp
from rlp import decode_lazy


def test_empty_list():
    dec = lambda: decode_lazy(rlp.encode([]))
    assert isinstance(dec(), Sequence) 
    with pytest.raises(IndexError):
        dec()[0]
    with pytest.raises(IndexError):
        dec()[1]
    assert len(dec()) == 0


def test_string():
    for s in ('', 'asdf', 'a' * 56, 'b' * 123):
        dec = lambda: decode_lazy(rlp.encode(s))
        assert isinstance(dec(), str)
        assert len(dec()) == len(s)
        assert dec() == s


def test_nested_list():
    l = [[], ['a'], ['b', 'c', 'd']]
    dec = lambda: decode_lazy(rlp.encode(l))
    assert isinstance(dec(), Sequence)
    assert len(dec()) == len(l)
    assert list(dec()[0]) == l[0]
    assert list(dec()[1]) == l[1]
    assert list(dec()[2]) == l[2]
    with pytest.raises(IndexError):
        assert dec()[0][0]
    assert dec()[1][0] == l[1][0]
    with pytest.raises(IndexError):
        assert dec()[1][1]
    assert dec()[2][0] == l[2][0]
    assert dec()[2][1] == l[2][1]
    assert dec()[2][2] == l[2][2]
    with pytest.raises(IndexError):
        assert dec()[2][3]
    with pytest.raises(IndexError):
        assert dec()[3]
