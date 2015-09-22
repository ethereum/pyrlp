import pytest
from rlp import SerializationError
from rlp import infer_sedes, Serializable, encode, decode, make_immutable
from rlp.sedes import big_endian_int, binary, List


class Test1(Serializable):
    fields = [
        ('field1', big_endian_int),
        ('field2', binary),
        ('field3', List((big_endian_int, binary)))
    ]


class Test2(Serializable):
    fields = [
        ('field1', Test1),
        ('field2', List((Test1, Test1))),
    ]


def test_serializable():
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

    # mutability
    test1a.field1 += 1
    test1a.field2 = 'x'
    assert test1a.field1 == 6
    assert test1a.field2 == 'x'
    test1a.field1 -= 1
    test1a.field2 = 'a'
    assert test1a.field1 == 5
    assert test1a.field2 == 'a'

    # inference
    assert infer_sedes(test1a) == Test1
    assert infer_sedes(test1b) == Test1
    assert infer_sedes(test2) == Test2

    # serialization
    with pytest.raises(SerializationError):
        Test1.serialize(test2)
    with pytest.raises(SerializationError):
        Test2.serialize(test1a)
    with pytest.raises(SerializationError):
        Test2.serialize(test1b)
    serial_1a = Test1.serialize(test1a)
    serial_1b = Test1.serialize(test1b)
    serial_2 = Test2.serialize(test2)
    assert serial_1a == [b'\x05', b'a', [b'', b'']]
    assert serial_1b == [b'\x09', b'b', [b'\x02', b'']]
    assert serial_2 == [serial_1a, [serial_1a, serial_1b]]

    # deserialization
    test1a_d = Test1.deserialize(serial_1a)
    test1b_d = Test1.deserialize(serial_1b)
    test2_d = Test2.deserialize(serial_2)
    assert not test1a_d.is_mutable()
    assert not test1b_d.is_mutable()
    assert not test2_d.is_mutable()
    for obj in (test1a_d, test1b_d):
        before1 = obj.field1
        before2 = obj.field2
        with pytest.raises(ValueError):
            obj.field1 += 1
        with pytest.raises(ValueError):
            obj.field2 = 'x'
        assert obj.field1 == before1
        assert obj.field2 == before2
    assert test1a_d == test1a
    assert test1b_d == test1b
    assert test2_d == test2

    # encoding and decoding
    for obj in (test1a, test1b, test2):
        rlp_code = encode(obj)
        assert obj._cached_rlp is None
        assert obj.is_mutable()

        assert encode(obj, cache=True) == rlp_code
        assert obj._cached_rlp == rlp_code
        assert not obj.is_mutable()

        assert encode(obj, cache=True) == rlp_code
        assert obj._cached_rlp == rlp_code
        assert not obj.is_mutable()

        assert encode(obj) == rlp_code
        assert obj._cached_rlp == rlp_code
        assert not obj.is_mutable()

        obj_decoded = decode(rlp_code, obj.__class__)
        assert obj_decoded == obj
        assert not obj_decoded.is_mutable()
        assert obj_decoded._cached_rlp == rlp_code


def test_make_immutable():
    assert make_immutable(1) == 1
    assert make_immutable('a') == 'a'
    assert make_immutable((1, 2, 3)) == (1, 2, 3)
    assert make_immutable([1, 2, 'a']) == (1, 2, 'a')
    assert make_immutable([[1], [2, [3], 4], 5, 6]) == ((1,), (2, (3,), 4), 5, 6)

    t1a_data = (5, 'a', (0, ''))
    t1b_data = (9, 'b', (2, ''))
    test1a = Test1(*t1a_data)
    test1b = Test1(*t1b_data)
    test2 = Test2(test1a, [test1a, test1b])

    assert test2.is_mutable()
    assert test2.field1.is_mutable()
    assert test2.field2[0].is_mutable()
    assert test2.field2[1].is_mutable()
    test2.make_immutable()
    assert not test2.is_mutable()
    assert not test1a.is_mutable()
    assert not test1b.is_mutable()
    assert test2.field1 == test1a
    assert test2.field2 == (test1a, test1b)

    test1a = Test1(*t1a_data)
    test1b = Test1(*t1b_data)
    test2 = Test2(test1a, [test1a, test1b])
    assert test2.is_mutable()
    assert test2.field1.is_mutable()
    assert test2.field2[0].is_mutable()
    assert test2.field2[1].is_mutable()
    assert make_immutable([test1a, [test2, test1b]]) == (test1a, (test2, test1b))
    assert not test2.is_mutable()
    assert not test1a.is_mutable()
    assert not test1b.is_mutable()
