import pytest

from rlp import SerializationError
from rlp import infer_sedes, encode, decode, make_immutable, make_mutable
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


_type_1_a = RLPType1(5, b'a', (0, b''))
_type_1_b = RLPType1(9, b'b', (2, b''))
_type_2 = RLPType2(_type_1_a, [_type_1_a, _type_1_b])


@pytest.fixture
def im_type_1_a():
    return _type_1_a.as_immutable()


@pytest.fixture
def im_type_1_b():
    return _type_1_b.as_immutable()


@pytest.fixture
def im_type_2():
    return _type_2.as_immutable()


@pytest.fixture
def type_1_a(im_type_1_a):
    return im_type_1_a.as_mutable()


@pytest.fixture
def type_1_b(im_type_1_b):
    return im_type_1_b.as_mutable()


@pytest.fixture
def type_2(im_type_2):
    return im_type_2.as_mutable()


@pytest.fixture(params=[_type_1_a, _type_1_b, _type_2])
def rlp_obj(request):
    return request.param.as_immutable().as_mutable()


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


def test_serializable_field_mutability(type_1_a):
    type_1_a.field1 += 1
    type_1_a.field2 = b'x'
    assert type_1_a.field1 == 6
    assert type_1_a.field2 == b'x'
    type_1_a.field1 -= 1
    type_1_a.field2 = b'a'
    assert type_1_a.field1 == 5
    assert type_1_a.field2 == b'a'


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
    im_type_1_a = type_1_a.as_immutable()

    with pytest.raises(AttributeError, match=r"can't set attribute"):
        im_type_1_a.field1 += 1
    assert im_type_1_a.field1 == 5

    with pytest.raises(AttributeError, match=r"can't set attribute"):
        im_type_1_a.field2 = b'x'
    assert im_type_1_a.field2 == b'a'

    assert im_type_1_a == type_1_a

    im_type_2 = type_2.as_immutable()

    with pytest.raises(AttributeError, match=r"can't set attribute"):
        im_type_2.field2_1.field1 += 1
    assert im_type_2.field2_1.field1 == 5

    with pytest.raises(TypeError, match=r"'tuple' object does not support item assignment"):
        im_type_2.field2_2[1] = type_1_a
    assert im_type_2.field2_2[1] == type_1_b

    assert im_type_2 == type_2


def test_serializable_encoding_rlp_caching(rlp_obj):
    assert rlp_obj._cached_rlp is None

    # obj should start out without a cache
    rlp_code = encode(rlp_obj, cache=False)
    assert rlp_obj._cached_rlp is None
    assert rlp_obj.is_mutable is True

    # cache should be populated now.
    assert encode(rlp_obj, cache=True) == rlp_code
    assert rlp_obj._cached_rlp == rlp_code
    assert rlp_obj.is_mutable is True

    # cache should still be populated and encoding should used cached_rlp value
    rlp_obj._cached_rlp = b'test-uses-cache'
    assert encode(rlp_obj, cache=True) == b'test-uses-cache'

    obj_decoded = decode(rlp_code, sedes=rlp_obj.__class__)
    assert obj_decoded == rlp_obj
    assert obj_decoded.is_immutable is True
    assert obj_decoded._cached_rlp == rlp_code


def test_serialiable_mutable_simple_object_rlp_cache_invalidation(type_1_a):
    assert type_1_a._cached_rlp is None
    rlp_code = encode(type_1_a, cache=True)
    assert type_1_a._cached_rlp == rlp_code

    # setting a field on the obj should invalidate the cache
    type_1_a.field1 = 12345
    assert type_1_a._cached_rlp is None


def assert_mutability(obj, is_mutable):
    if isinstance(obj, Serializable):
        assert obj.is_mutable is is_mutable
        assert obj.is_immutable is not is_mutable
        for value in obj:
            assert_mutability(value, is_mutable)
    elif isinstance(obj, (list, tuple)):
        if is_mutable:
            assert isinstance(obj, list)
        else:
            assert isinstance(obj, tuple)
        for item in obj:
            assert_mutability(item, is_mutable)


def test_serializable_as_immutable(type_1_a, type_1_b, type_2):
    assert make_immutable(1) == 1
    assert make_immutable(b'a') == b'a'
    assert make_immutable((1, 2, 3)) == (1, 2, 3)
    assert make_immutable([1, 2, b'a']) == (1, 2, b'a')
    assert make_immutable([[1], [2, [3], 4], 5, 6]) == ((1,), (2, (3,), 4), 5, 6)

    assert_mutability(type_2, True)
    assert_mutability(type_1_a, True)
    assert_mutability(type_1_b, True)

    im_type_2 = type_2.as_immutable()

    assert im_type_2 == type_2
    assert im_type_2.field2_1 == type_1_a
    assert im_type_2.field2_2[0] == type_1_a
    assert im_type_2.field2_2[1] == type_1_b

    # original mutability should not have changed
    assert_mutability(type_2, True)
    assert_mutability(type_1_a, True)
    assert_mutability(type_1_b, True)

    # new obj should be mutable
    assert_mutability(im_type_2, False)


def test_serializable_as_mutable(im_type_1_a, im_type_1_b, im_type_2):
    assert make_mutable(1) == 1
    assert make_mutable(b'a') == b'a'
    assert make_mutable((1, 2, 3)) == [1, 2, 3]
    assert make_mutable([1, 2, b'a']) == [1, 2, b'a']
    assert make_mutable([[1], [2, [3], 4], 5, 6]) == [[1], [2, [3], 4], 5, 6]

    assert_mutability(im_type_2, False)
    assert_mutability(im_type_1_a, False)
    assert_mutability(im_type_1_b, False)

    type_2 = im_type_2.as_mutable()

    assert type_2 == im_type_2
    assert type_2.field2_1 == im_type_1_a
    assert type_2.field2_2[0] == im_type_1_a
    assert type_2.field2_2[1] == im_type_1_b

    # original mutability should not have changed
    assert_mutability(im_type_2, False)
    assert_mutability(im_type_1_a, False)
    assert_mutability(im_type_1_b, False)

    # new obj should be mutable
    assert_mutability(type_2, True)


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
