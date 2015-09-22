from collections import Sequence
import pytest
import rlp
from rlp import DeserializationError
from rlp.sedes import big_endian_int, CountableList


def evaluate(lazy_list):
    if isinstance(lazy_list, rlp.lazy.LazyList):
        return tuple(evaluate(e) for e in lazy_list)
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
    assert evaluate(dec()) == ()


def test_string():
    for s in (b'', b'asdf', b'a' * 56, b'b' * 123):
        dec = lambda: rlp.decode_lazy(rlp.encode(s))
        assert isinstance(dec(), bytes)
        assert len(dec()) == len(s)
        assert dec() == s
        assert rlp.peek(rlp.encode(s), []) == s
        with pytest.raises(IndexError):
            rlp.peek(rlp.encode(s), 0)
        with pytest.raises(IndexError):
            rlp.peek(rlp.encode(s), [0])


def test_nested_list():
    l = ((), (b'a'), (b'b', b'c', b'd'))
    dec = lambda: rlp.decode_lazy(rlp.encode(l))
    assert isinstance(dec(), Sequence)
    assert len(dec()) == len(l)
    assert evaluate(dec()) == l
    with pytest.raises(IndexError):
        dec()[0][0]
    with pytest.raises(IndexError):
        dec()[1][1]
    with pytest.raises(IndexError):
        dec()[2][3]
    with pytest.raises(IndexError):
        dec()[3]


def test_sedes():
    ls = [
        (),
        (1,),
        (3, 2, 1)
    ]
    for l in ls:
        assert evaluate(rlp.decode_lazy(rlp.encode(l), big_endian_int)) == l

    sedes = CountableList(big_endian_int)
    l = [(), (1, 2), 'asdf', (3)]
    invalid_lazy = rlp.decode_lazy(rlp.encode(l), sedes)
    assert invalid_lazy[0] == l[0]
    assert invalid_lazy[1] == l[1]
    with pytest.raises(DeserializationError):
        invalid_lazy[2]


def test_peek():
    assert rlp.peek(rlp.encode(b''), []) == b''
    nested = rlp.encode([0, 1, [2, 3]])
    assert rlp.peek(nested, [2, 0], big_endian_int) == 2
    for index in [3, [3], [0, 0], [2, 2], [2, 1, 0]]:
        with pytest.raises(IndexError):
            rlp.peek(nested, index)
    assert rlp.peek(nested, 2, CountableList(big_endian_int)) == (2, 3)
