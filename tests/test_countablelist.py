from rlp.sedes import big_endian_int
from rlp.sedes.lists import CountableList


def test_countable_list():
    l1 = CountableList(big_endian_int)
    serializable = ([], [1, 2], list(xrange(500)))
    for s in serializable:
        assert l1.serializable(s)
        assert l1.deserialize(l1.serialize(s)) == s
    not_serializable = ([1, 'asdf'], ['asdf'], [1, [2]], [[]])
    for n in not_serializable:
        assert not l1.serializable(n)

    l2 = CountableList(CountableList(big_endian_int))
    serializable = ([], [[]], [[1, 2, 3], [4]], [[5], [6, 7, 8]], [[], [],
                    [9, 0]])
    for s in serializable:
        assert l2.serializable(s)
        assert l2.deserialize(l2.serialize(s)) == s
    not_serializable = ([[[]]], [1, 2], [1, ['asdf'], ['fdsa']])
    for n in not_serializable:
        assert not l2.serializable(n)

