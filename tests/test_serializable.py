import pytest

from rlp import SerializationError
from rlp import infer_sedes, encode, decode
from rlp.sedes import big_endian_int, binary, List
from rlp.sedes.serializable import Serializable


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


class RLPType3(Serializable):
    fields = [
        ('field1', big_endian_int),
        ('field2', big_endian_int),
        ('field3', big_endian_int),
    ]

    def __init__(self, field2, field1, field3, **kwargs):
        super().__init__(field1=field1, field2=field2, field3=field3, **kwargs)


class RLPType4(RLPType3):
    pass


_type_1_a = RLPType1(5, b'a', (0, b''))
_type_1_b = RLPType1(9, b'b', (2, b''))
_type_2 = RLPType2(_type_1_a, [_type_1_a, _type_1_b])


@pytest.fixture
def type_1_a():
    return _type_1_a


@pytest.fixture
def type_1_b():
    return _type_1_b


@pytest.fixture
def type_2():
    return _type_2


@pytest.fixture(params=[_type_1_a, _type_1_b, _type_2])
def rlp_obj(request):
    return request.param


@pytest.mark.parametrize(
    'rlptype,args,kwargs,exception_includes',
    (
        # missing fields args
        (RLPType1, [], {}, ['field1', 'field2', 'field3']),
        (RLPType1, [8], {}, ['field2', 'field3']),
        (RLPType1, [7, 8], {}, ['field3']),
        # missing fields kwargs
        (RLPType1, [], {'field1': 7}, ['field2', 'field3']),
        (RLPType1, [], {'field1': 7, 'field2': 8}, ['field3']),
        (RLPType1, [], {'field2': 7, 'field3': (1, b'')}, ['field1']),
        (RLPType1, [], {'field3': (1, b'')}, ['field1', 'field2']),
        (RLPType1, [], {'field2': 7}, ['field1', 'field3']),
        # missing fields args and kwargs
        (RLPType1, [7], {'field2': 8}, ['field3']),
        (RLPType1, [7], {'field3': (1, b'')}, ['field2']),
        # duplicate fields
        (RLPType1, [7], {'field1': 8}, ['field1']),
        (RLPType1, [7, 8], {'field1': 8, 'field2': 7}, ['field1', 'field2']),
    ),
)
def test_serializable_initialization_validation(rlptype, args, kwargs, exception_includes):
    for msg_part in exception_includes:
        with pytest.raises(TypeError, match=msg_part):
            rlptype(*args, **kwargs)


@pytest.mark.parametrize(
    'args,kwargs',
    (
        ([2, 1, 3], {}),
        ([2, 1], {'field3': 3}),
        ([2], {'field3': 3, 'field1': 1}),
        ([], {'field3': 3, 'field1': 1, 'field2': 2}),
    ),
)
def test_serializable_initialization_args_kwargs_mix(args, kwargs):
    obj = RLPType3(*args, **kwargs)

    assert obj.field1 == 1
    assert obj.field2 == 2
    assert obj.field3 == 3


def test_serializable_subclass_retains_field_info_from_parent():
    obj = RLPType4(2, 1, 3)
    assert obj.field1 == 1
    assert obj.field2 == 2
    assert obj.field3 == 3


def test_deserialization_for_custom_init_method():
    type_3 = RLPType3(2, 1, 3)
    assert type_3.field1 == 1
    assert type_3.field2 == 2
    assert type_3.field3 == 3

    result = decode(encode(type_3), sedes=RLPType3)

    assert result.field1 == 1
    assert result.field2 == 2
    assert result.field3 == 3


def test_serializable_iterator():
    values = (5, b'a', (1, b'c'))
    obj = RLPType1(*values)
    assert tuple(obj) == values


def test_serializable_equality(type_1_a, type_1_b, type_2):
    # equality
    assert type_1_a == type_1_a
    assert type_1_a == RLPType1(*type_1_a)
    assert type_1_b == type_1_b
    assert type_1_b == RLPType1(*type_1_b)

    assert type_2 == type_2
    assert type_1_a != type_1_b
    assert type_1_b != type_2
    assert type_2 != type_1_a


def test_serializable_sedes_inference(type_1_a, type_1_b, type_2):
    assert infer_sedes(type_1_a) == RLPType1
    assert infer_sedes(type_1_b) == RLPType1
    assert infer_sedes(type_2) == RLPType2


def test_serializable_invalid_serialization_value(type_1_a, type_1_b, type_2):
    with pytest.raises(SerializationError):
        RLPType1.serialize(type_2)
    with pytest.raises(SerializationError):
        RLPType2.serialize(type_1_a)
    with pytest.raises(SerializationError):
        RLPType2.serialize(type_1_b)


def test_serializable_serialization(type_1_a, type_1_b, type_2):
    serial_1_a = RLPType1.serialize(type_1_a)
    serial_1_b = RLPType1.serialize(type_1_b)
    serial_2 = RLPType2.serialize(type_2)
    assert serial_1_a == [b'\x05', b'a', [b'', b'']]
    assert serial_1_b == [b'\x09', b'b', [b'\x02', b'']]
    assert serial_2 == [serial_1_a, [serial_1_a, serial_1_b]]


def test_serializable_deserialization(type_1_a, type_1_b, type_2):
    serial_1_a = RLPType1.serialize(type_1_a)
    serial_1_b = RLPType1.serialize(type_1_b)
    serial_2 = RLPType2.serialize(type_2)

    res_type_1_a = RLPType1.deserialize(serial_1_a)
    res_type_1_b = RLPType1.deserialize(serial_1_b)
    res_type_2 = RLPType2.deserialize(serial_2)

    assert res_type_1_a == type_1_a
    assert res_type_1_b == type_1_b
    assert res_type_2 == type_2


def test_serializable_field_immutability(type_1_a, type_1_b, type_2):
    with pytest.raises(AttributeError, match=r"can't set attribute"):
        type_1_a.field1 += 1
    assert type_1_a.field1 == 5

    with pytest.raises(AttributeError, match=r"can't set attribute"):
        type_1_a.field2 = b'x'
    assert type_1_a.field2 == b'a'

    with pytest.raises(AttributeError, match=r"can't set attribute"):
        type_2.field2_1.field1 += 1
    assert type_2.field2_1.field1 == 5

    with pytest.raises(TypeError, match=r"'tuple' object does not support item assignment"):
        type_2.field2_2[1] = type_1_a
    assert type_2.field2_2[1] == type_1_b


def test_serializable_encoding_rlp_caching(rlp_obj):
    assert rlp_obj._cached_rlp is None

    # obj should start out without a cache
    rlp_code = encode(rlp_obj, cache=False)
    assert rlp_obj._cached_rlp is None

    # cache should be populated now.
    assert encode(rlp_obj, cache=True) == rlp_code
    assert rlp_obj._cached_rlp == rlp_code

    # cache should still be populated and encoding should used cached_rlp value
    rlp_obj._cached_rlp = b'test-uses-cache'
    assert encode(rlp_obj, cache=True) == b'test-uses-cache'

    obj_decoded = decode(rlp_code, sedes=rlp_obj.__class__)
    assert obj_decoded == rlp_obj
    assert obj_decoded._cached_rlp == rlp_code


def test_serializable_inheritance():
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
