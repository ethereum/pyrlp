import pytest
import rlp
from rlp.sedes import big_endian_int
from rlp.sedes.lists import CountableList
from rlp import SerializationError, DeserializationError


def test_countable_list():
    l1 = CountableList(big_endian_int)
    serializable = [(), (1, 2), tuple(range(500))]
    for s in serializable:
        r = l1.serialize(s)
        assert l1.deserialize(r) == s
    not_serializable = ([1, 'asdf'], ['asdf'], [1, [2]], [[]])
    for n in not_serializable:
        with pytest.raises(SerializationError):
            l1.serialize(n)

    l2 = CountableList(CountableList(big_endian_int))
    serializable = ((), ((),), ((1, 2, 3), (4,)), ((5,), (6, 7, 8)), ((), (),
                    (9, 0)))
    for s in serializable:
        r = l2.serialize(s)
        assert l2.deserialize(r) == s
    not_serializable = ([[[]]], [1, 2], [1, ['asdf'], ['fdsa']])
    for n in not_serializable:
        with pytest.raises(SerializationError):
            l2.serialize(n)

    l3 = CountableList(big_endian_int, max_length=3)
    serializable = [(), (1,), (1, 2), (1, 2, 3)]
    for s in serializable:
        r = l3.serialize(s)
        assert r == l1.serialize(s)
        assert l3.deserialize(r) == s
    not_serializable = [(1, 2, 3, 4), (1, 2, 3, 4, 5, 6, 7), range(500)]
    for s in not_serializable:
        with pytest.raises(SerializationError):
            l3.serialize(s)
        r = l1.serialize(s)
        with pytest.raises(DeserializationError):
            l3.deserialize(r)
        ll = rlp.decode_lazy(rlp.encode(r))
        with pytest.raises(DeserializationError):
            l3.deserialize(ll)
        assert len(ll._elements) == 3 + 1  # failed early, did not consume fully
