import pytest
from rlp import SerializationError, DeserializationError
from rlp import infer_sedes
from rlp.sedes import big_endian_int, binary, List, CountableList


def test_inference():
    obj_sedes_pairs = (
        (5, big_endian_int),
        (0, big_endian_int),
        (-1, None),
        ('', binary),
        ('asdf', binary),
        ('\xe4\xf6\xfc\xea\xe2\xfb', binary),
        ([], List()),
        ([1, 2, 3], List((big_endian_int,) * 3)),
        ([[], 'asdf'], List(([], binary))),
    )

    for obj, sedes in obj_sedes_pairs:
        if sedes is not None:
            inferred = infer_sedes(obj)
            assert inferred == sedes
            sedes.serialize(obj)
        else:
            with pytest.raises(TypeError):
                infer_sedes(obj)


def test_list_sedes():
    l1 = List()
    l2 = List((big_endian_int, big_endian_int))
    l3 = List((l1, l2, [[[]]]))

    l1.serialize([])
    l2.serialize((2, 3))
    l3.serialize([[], [5, 6], [[[]]]])

    with pytest.raises(SerializationError):
        l1.serialize([[]])
    with pytest.raises(SerializationError):
        l1.serialize([5])

    for d in ([], [1, 2, 3], [1, [2, 3], 4]):
        with pytest.raises(SerializationError):
            l2.serialize(d)
    for d in ([], [[], [], [[[]]]], [[], [5, 6], [[]]]):
        with pytest.raises(SerializationError):
            l3.serialize(d)

    c = CountableList(big_endian_int)
    assert l1.deserialize(c.serialize([])) == ()
    for s in (c.serialize(l) for l in [[1], [1, 2, 3], range(30), (4, 3)]):
        with pytest.raises(DeserializationError):
            l1.deserialize(s)

    valid = [(1, 2), (3, 4), (9, 8)]
    for s, v in ((c.serialize(v), v) for v in valid):
        assert l2.deserialize(s) == v
    invalid = [[], [1], [1, 2, 3]]
    for s in (c.serialize(i) for i in invalid):
        with pytest.raises(DeserializationError):
            l2.deserialize(s)
