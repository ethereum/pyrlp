import pytest
from rlp import SerializationError
from rlp import infer_sedes, Serializable, encode, decode, make_immutable, make_mutable
from rlp.sedes import big_endian_int, binary, List


class RLPType1(Serializable):
    fields = [
        ('field1', big_endian_int),
        ('field2', binary),
        ('field3', List((big_endian_int, binary)))
    ]


class RLPType2(Serializable):
    fields = [
        ('field2_1', RLPType1),
        ('field2_2', List((RLPType1, RLPType1))),
    ]


@pytest.mark.parametrize(
    'rlptype, fields, exception_includes',
    (
        (RLPType1, [8], 'field2'),
        (RLPType1, [8], 'field3'),
        (RLPType2, [], 'field2_1'),
        (RLPType2, [], 'field2_2'),
        (RLPType2, [RLPType1(8, 'a', (7, ''))], 'field2_2'),
    ),
)
def test_validation(rlptype, fields, exception_includes):
    with pytest.raises(TypeError, match=exception_includes):
        rlptype(*fields)


def test_serializable():
    t1a_data = (5, 'a', (0, ''))
    t1b_data = (9, 'b', (2, ''))
    test1a = RLPType1(*t1a_data)
    test1b = RLPType1(*t1b_data)
    test2 = RLPType2(test1a, [test1a, test1b])

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
    assert infer_sedes(test1a) == RLPType1
    assert infer_sedes(test1b) == RLPType1
    assert infer_sedes(test2) == RLPType2

    # serialization
    with pytest.raises(SerializationError):
        RLPType1.serialize(test2)
    with pytest.raises(SerializationError):
        RLPType2.serialize(test1a)
    with pytest.raises(SerializationError):
        RLPType2.serialize(test1b)
    serial_1a = RLPType1.serialize(test1a)
    serial_1b = RLPType1.serialize(test1b)
    serial_2 = RLPType2.serialize(test2)
    assert serial_1a == [b'\x05', b'a', [b'', b'']]
    assert serial_1b == [b'\x09', b'b', [b'\x02', b'']]
    assert serial_2 == [serial_1a, [serial_1a, serial_1b]]

    # deserialization
    test1a_d = RLPType1.deserialize(serial_1a)
    test1b_d = RLPType1.deserialize(serial_1b)
    test2_d = RLPType2.deserialize(serial_2, mutable=True)
    assert not test1a_d.is_mutable()
    assert not test1b_d.is_mutable()
    assert test2_d.is_mutable()
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
    test1a = RLPType1(*t1a_data)
    test1b = RLPType1(*t1b_data)
    test2 = RLPType2(test1a, [test1a, test1b])

    assert test2.is_mutable()
    assert test2.field2_1.is_mutable()
    assert test2.field2_2[0].is_mutable()
    assert test2.field2_2[1].is_mutable()
    test2.make_immutable()
    assert not test2.is_mutable()
    assert not test1a.is_mutable()
    assert not test1b.is_mutable()
    assert test2.field2_1 == test1a
    assert test2.field2_2 == (test1a, test1b)

    test1a = RLPType1(*t1a_data)
    test1b = RLPType1(*t1b_data)
    test2 = RLPType2(test1a, [test1a, test1b])
    assert test2.is_mutable()
    assert test2.field2_1.is_mutable()
    assert test2.field2_2[0].is_mutable()
    assert test2.field2_2[1].is_mutable()
    assert make_immutable([test1a, [test2, test1b]]) == (test1a, (test2, test1b))
    assert not test2.is_mutable()
    assert not test1a.is_mutable()
    assert not test1b.is_mutable()


def test_make_mutable():
    assert make_mutable(1) == 1
    assert make_mutable('a') == 'a'
    assert make_mutable((1, 2, 3)) == [1, 2, 3]
    assert make_mutable([1, 2, 'a']) == [1, 2, 'a']
    assert make_mutable([[1], [2, [3], 4], 5, 6]) == [[1], [2, [3], 4], 5, 6]

    t1a_data = (5, 'a', (0, ''))
    t1b_data = (9, 'b', (2, ''))
    test1a = RLPType1(*t1a_data)
    test1b = RLPType1(*t1b_data)
    test2 = RLPType2(test1a, [test1a, test1b])

    test1a.make_immutable()
    test1b.make_immutable()
    test2.make_immutable()

    assert not test2.is_mutable()
    assert not test2.field2_1.is_mutable()
    assert not test2.field2_2[0].is_mutable()
    assert not test2.field2_2[1].is_mutable()
    test2.make_mutable()
    assert test2.is_mutable()
    assert test2.field2_2[0].is_mutable()
    assert test2.field2_2[1].is_mutable()
    assert test1a.is_mutable()
    assert test1b.is_mutable()
    assert test2.field2_1 == test1a
    assert test2.field2_2 == [test1a, test1b]

    test1a = RLPType1(*t1a_data)
    test1b = RLPType1(*t1b_data)
    test2 = RLPType2(test1a, [test1a, test1b])

    test1a.make_immutable()
    test1b.make_immutable()
    test2.make_immutable()

    assert not test2.is_mutable()
    assert not test2.field2_1.is_mutable()
    assert not test2.field2_2[0].is_mutable()
    assert not test2.field2_2[1].is_mutable()
    assert make_mutable([test1a, [test2, test1b]]) == [test1a, [test2, test1b]]
    assert test2.is_mutable()
    assert test1a.is_mutable()
    assert test1b.is_mutable()


def test_inheritance():
    class Parent(Serializable):
        fields = (
            ('field1', big_endian_int),
            ('field2', big_endian_int),
        )

    class Child1(Parent):
        fields = (
            ('field1', big_endian_int),
            ('field2', big_endian_int),
            ('field3', big_endian_int),
        )

    class Child2(Parent):
        fields = (
            ('field1', big_endian_int),
        )

    class Child3(Parent):
        fields = (
            ('new_field1', big_endian_int),
            ('field2', big_endian_int),
        )

    class Child4(Parent):
        fields = (
            ('field1', binary),
            ('field2', binary),
            ('field3', big_endian_int),
        )

    p = Parent(1, 2)
    c1 = Child1(1, 2, 3)
    c2 = Child2(1)
    c3 = Child3(1, 2)
    c4 = Child4(b'a', b'b', 5)

    assert Parent.serialize(p) == [b'\x01', b'\x02']
    assert Child1.serialize(c1) == [b'\x01', b'\x02', b'\x03']
    assert Child2.serialize(c2) == [b'\x01']
    assert Child3.serialize(c3) == [b'\x01', b'\x02']
    assert Child4.serialize(c4) == [b'a', b'b', b'\x05']

    with pytest.raises(AttributeError):
        p.field3
    with pytest.raises(AttributeError):
        p.new_field1

    with pytest.raises(AttributeError):
        c2.field2
    with pytest.raises(AttributeError):
        c2.new_field1

    with pytest.raises(AttributeError):
        c3.field1
    with pytest.raises(AttributeError):
        c3.field3
