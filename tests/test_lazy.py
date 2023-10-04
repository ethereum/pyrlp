from collections.abc import (
    Sequence,
)

import pytest

import rlp
from rlp import (
    DeserializationError,
)
from rlp.sedes import (
    CountableList,
    big_endian_int,
)


def evaluate(lazy_list):
    if isinstance(lazy_list, rlp.lazy.LazyList):
        return tuple(evaluate(e) for e in lazy_list)
    else:
        return lazy_list


def test_empty_list():
    def dec():
        return rlp.decode_lazy(rlp.encode([]))

    assert isinstance(dec(), Sequence)
    with pytest.raises(IndexError):
        dec()[0]
    with pytest.raises(IndexError):
        dec()[1]
    assert len(dec()) == 0
    assert evaluate(dec()) == ()


@pytest.mark.parametrize(
    "value",
    (b"", b"asdf", b"a" * 56, b"b" * 123),
)
def test_string(value):
    def dec():
        return rlp.decode_lazy(rlp.encode(value))

    assert isinstance(dec(), bytes)
    assert len(dec()) == len(value)
    assert dec() == value
    assert rlp.peek(rlp.encode(value), []) == value
    with pytest.raises(IndexError):
        rlp.peek(rlp.encode(value), 0)
    with pytest.raises(IndexError):
        rlp.peek(rlp.encode(value), [0])


def test_list_getitem():
    length = rlp.decode_lazy(rlp.encode([1, 2, 3]), big_endian_int)
    assert isinstance(length, rlp.lazy.LazyList)
    assert length[0] == 1
    assert length[1] == 2
    assert length[2] == 3
    assert length[-1] == 3
    assert length[-2] == 2
    assert length[-3] == 1
    assert length[0:3] == [1, 2, 3]
    assert length[0:2] == [1, 2]
    assert length[0:1] == [1]
    assert length[1:2] == [2]
    assert length[1:] == [2, 3]
    assert length[1:-1] == [2]
    assert length[-2:] == [2, 3]
    assert length[:2] == [1, 2]


def test_nested_list():
    length = ((), (b"a"), (b"b", b"c", b"d"))

    def dec():
        return rlp.decode_lazy(rlp.encode(length))

    assert isinstance(dec(), Sequence)
    assert len(dec()) == len(length)
    assert evaluate(dec()) == length
    with pytest.raises(IndexError):
        dec()[0][0]
    with pytest.raises(IndexError):
        dec()[1][1]
    with pytest.raises(IndexError):
        dec()[2][3]
    with pytest.raises(IndexError):
        dec()[3]


@pytest.mark.parametrize(
    "value",
    (
        (),
        (1,),
        (3, 2, 1),
    ),
)
def test_evaluation_of_lazy_decode_with_simple_value_sedes(value):
    assert evaluate(rlp.decode_lazy(rlp.encode(value), big_endian_int)) == value


def test_evaluation_of_lazy_decode_with_list_sedes_and_invalid_value():
    sedes = CountableList(big_endian_int)
    value = [(), (1, 2), b"asdf", (3)]
    invalid_lazy = rlp.decode_lazy(rlp.encode(value), sedes)
    assert invalid_lazy[0] == value[0]
    assert invalid_lazy[1] == value[1]
    with pytest.raises(DeserializationError):
        invalid_lazy[2]


def test_peek():
    assert rlp.peek(rlp.encode(b""), []) == b""
    nested = rlp.encode([0, 1, [2, 3]])
    assert rlp.peek(nested, [2, 0], big_endian_int) == 2
    for index in [3, [3], [0, 0], [2, 2], [2, 1, 0]]:
        with pytest.raises(IndexError):
            rlp.peek(nested, index)
    assert rlp.peek(nested, 2, CountableList(big_endian_int)) == (2, 3)
