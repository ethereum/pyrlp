import pytest
from rlp import SerializationError
from rlp import infer_sedes, Serializable, encode, decode
from rlp.sedes import big_endian_int, binary, List


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


def test_serializable():
    class Test1(Serializable):
        fields = (
            ('field1', big_endian_int),
            ('field2', binary),
            ('field3', List((big_endian_int, binary)))
        )

    class Test2(Serializable):
        fields = (
            ('field1', Test1),
            ('field2', List((Test1, Test1))),
        )

    t1a_data = (5, 'a', (0, ''))
    t1b_data = (9, 'b', (2, ''))
    test1a = Test1(*t1a_data)
    test1b = Test1(*t1b_data)
    test2 = Test2(test1a, [test1a, test1b])

    # equality
    assert test1a == test1a
    assert test1b == test1b
    assert test2 == test2
    assert test1a != test1b
    assert test1b != test2
    assert test2 != test1a

    with pytest.raises(SerializationError):
        Test1.serialize(test2)
    with pytest.raises(SerializationError):
        Test2.serialize(test1a)
    with pytest.raises(SerializationError):
        Test2.serialize(test1b)

    # inference
    assert infer_sedes(test1a) == Test1
    assert infer_sedes(test1b) == Test1
    assert infer_sedes(test2) == Test2

    # serialization
    serial_1a = Test1.serialize(test1a)
    serial_1b = Test1.serialize(test1b)
    serial_2 = Test2.serialize(test2)
    assert serial_1a == [b'\x05', b'a', [b'', b'']]
    assert serial_1b == [b'\x09', b'b', [b'\x02', b'']]
    assert serial_2 == [serial_1a, [serial_1a, serial_1b]]

    # deserialization
    assert Test1.deserialize(serial_1a) == test1a
    assert Test1.deserialize(serial_1b) == test1b
    assert Test2.deserialize(serial_2) == test2

    # encoding and decoding
    assert decode(encode(test1a), Test1) == test1a
    assert decode(encode(test1b), Test1) == test1b
    assert decode(encode(test2), Test2) == test2
