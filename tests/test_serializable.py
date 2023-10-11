from multiprocessing import (
    get_context,
)
import pickle
import re

import pytest

from rlp import (
    SerializationError,
    decode,
    encode,
    infer_sedes,
)
from rlp.sedes import (
    List,
    big_endian_int,
    binary,
)
from rlp.sedes.serializable import (
    Serializable,
)


class RLPType1(Serializable):
    fields = [
        ("field1", big_endian_int),
        ("field2", binary),
        ("field3", List((big_endian_int, binary))),
    ]


class RLPType2(Serializable):
    fields = [
        ("field2_1", RLPType1),
        ("field2_2", List((RLPType1, RLPType1))),
    ]


class RLPType3(Serializable):
    fields = [
        ("field1", big_endian_int),
        ("field2", big_endian_int),
        ("field3", big_endian_int),
    ]

    def __init__(self, field2, field1, field3, **kwargs):
        super().__init__(field1=field1, field2=field2, field3=field3, **kwargs)


class RLPType4(RLPType3):
    pass


class RLPEmptyFieldsType(Serializable):
    fields = ()


class RLPUndeclaredFieldsType(Serializable):
    pass


_type_1_a = RLPType1(5, b"a", (0, b""))
_type_1_b = RLPType1(9, b"b", (2, b""))
_type_2 = RLPType2(_type_1_a.copy(), [_type_1_a.copy(), _type_1_b.copy()])
_type_undeclared_fields = RLPUndeclaredFieldsType()


@pytest.fixture
def type_1_a():
    return _type_1_a.copy()


@pytest.fixture
def type_1_b():
    return _type_1_b.copy()


@pytest.fixture
def type_2():
    return _type_2.copy()


@pytest.fixture(params=[_type_1_a, _type_1_b, _type_2])
def rlp_obj(request):
    return request.param.copy()


def test_serializeable_repr_evaluatable(rlp_obj):
    evaluated = eval(repr(rlp_obj))
    assert evaluated == rlp_obj


@pytest.mark.parametrize(
    "rlptype,args,kwargs,exception_includes",
    (
        # missing fields args
        (RLPType1, [], {}, ["field1", "field2", "field3"]),
        (RLPType1, [8], {}, ["field2", "field3"]),
        (RLPType1, [7, 8], {}, ["field3"]),
        # missing fields kwargs
        (RLPType1, [], {"field1": 7}, ["field2", "field3"]),
        (RLPType1, [], {"field1": 7, "field2": 8}, ["field3"]),
        (RLPType1, [], {"field2": 7, "field3": (1, b"")}, ["field1"]),
        (RLPType1, [], {"field3": (1, b"")}, ["field1", "field2"]),
        (RLPType1, [], {"field2": 7}, ["field1", "field3"]),
        # missing fields args and kwargs
        (RLPType1, [7], {"field2": 8}, ["field3"]),
        (RLPType1, [7], {"field3": (1, b"")}, ["field2"]),
        # duplicate fields
        (RLPType1, [7], {"field1": 8}, ["field1"]),
        (RLPType1, [7, 8], {"field1": 8, "field2": 7}, ["field1", "field2"]),
    ),
)
def test_serializable_initialization_validation(
    rlptype, args, kwargs, exception_includes
):
    for msg_part in exception_includes:
        with pytest.raises(TypeError, match=msg_part):
            rlptype(*args, **kwargs)


@pytest.mark.parametrize(
    "args,kwargs",
    (
        ([2, 1, 3], {}),
        ([2, 1], {"field3": 3}),
        ([2], {"field3": 3, "field1": 1}),
        ([], {"field3": 3, "field1": 1, "field2": 2}),
    ),
)
def test_serializable_initialization_args_kwargs_mix(args, kwargs):
    obj = RLPType3(*args, **kwargs)

    assert obj.field1 == 1
    assert obj.field2 == 2
    assert obj.field3 == 3


@pytest.mark.parametrize(
    "lookup,expected",
    (
        (0, 5),
        (1, b"a"),
        (2, (0, b"")),
        (slice(0, 1), (5,)),
        (slice(0, 2), (5, b"a")),
        (slice(0, 3), (5, b"a", (0, b""))),
        (slice(1, 3), (b"a", (0, b""))),
        (slice(2, 3), ((0, b""),)),
        (slice(None, 3), (5, b"a", (0, b""))),
        (slice(None, 2), (5, b"a")),
        (slice(None, 1), (5,)),
        (slice(None, 0), tuple()),
        (slice(0, None), (5, b"a", (0, b""))),
        (slice(1, None), (b"a", (0, b""))),
        (slice(2, None), ((0, b""),)),
        (slice(2, None), ((0, b""),)),
        (slice(None, None), (5, b"a", (0, b""))),
        (slice(-1, None), ((0, b""),)),
        (
            slice(-2, None),
            (
                b"a",
                (0, b""),
            ),
        ),
        (
            slice(-3, None),
            (
                5,
                b"a",
                (0, b""),
            ),
        ),
    ),
)
def test_serializable_getitem_lookups(type_1_a, lookup, expected):
    actual = type_1_a[lookup]
    assert actual == expected


def test_serializable_subclass_retains_field_info_from_parent():
    obj = RLPType4(2, 1, 3)
    assert obj.field1 == 1
    assert obj.field2 == 2
    assert obj.field3 == 3


def test_undeclared_fields_serializable_class():
    assert RLPUndeclaredFieldsType.serialize(_type_undeclared_fields) == []
    assert (
        RLPUndeclaredFieldsType.deserialize(
            RLPUndeclaredFieldsType.serialize(_type_undeclared_fields)
        )
        == _type_undeclared_fields
    )


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
    values = (5, b"a", (1, b"c"))
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


def test_serializable_pickling_across_processes(type_1_a):
    # Ensure the hash is what we expect *and* populate the cache.
    assert hash(type_1_a) == hash(tuple(type_1_a))

    pickled_obj = pickle.dumps(type_1_a)
    for method in ["fork", "spawn"]:
        ctx = get_context(method)
        p = ctx.Process(target=_assert_hash_cache_equal, args=(pickled_obj,))
        p.start()
        p.join()


def _assert_hash_cache_equal(pickled_obj):
    obj = pickle.loads(pickled_obj)
    assert hash(obj) == hash(tuple(obj))


def test_serializable_sedes_inference(type_1_a, type_1_b, type_2):
    assert infer_sedes(type_1_a) == RLPType1
    assert infer_sedes(type_1_b) == RLPType1
    assert infer_sedes(type_2) == RLPType2


def test_serializable_invalid_serialization_value(type_1_a, type_1_b, type_2):
    # Note this is not done in parametrize because the values are pytest.fixtures
    value_fixtures = (
        (RLPType2, type_1_a),
        (RLPType2, type_1_b),
        (RLPType1, type_2),
        (RLPEmptyFieldsType, type_1_a),
        (RLPEmptyFieldsType, type_1_b),
        (RLPEmptyFieldsType, type_2),
    )
    for serializer, invalid_value in value_fixtures:
        with pytest.raises(SerializationError):
            serializer.serialize(invalid_value)


def test_serializable_serialization(type_1_a, type_1_b, type_2):
    serial_1_a = RLPType1.serialize(type_1_a)
    serial_1_b = RLPType1.serialize(type_1_b)
    serial_2 = RLPType2.serialize(type_2)
    assert serial_1_a == [b"\x05", b"a", [b"", b""]]
    assert serial_1_b == [b"\x09", b"b", [b"\x02", b""]]
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
        type_1_a.field2 = b"x"
    assert type_1_a.field2 == b"a"

    with pytest.raises(AttributeError, match=r"can't set attribute"):
        type_2.field2_1.field1 += 1
    assert type_2.field2_1.field1 == 5

    with pytest.raises(
        TypeError, match=r"'tuple' object does not support item assignment"
    ):
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
    rlp_obj._cached_rlp = b"test-uses-cache"
    assert encode(rlp_obj, cache=True) == b"test-uses-cache"

    obj_decoded = decode(rlp_code, sedes=rlp_obj.__class__)
    assert obj_decoded == rlp_obj
    assert obj_decoded._cached_rlp == rlp_code


def test_list_of_serializable_decoding_rlp_caching(rlp_obj):
    rlp_obj_code = encode(rlp_obj, cache=False)
    L = [rlp_obj, rlp_obj]
    list_code = encode(L, cache=False)

    L2 = decode(
        list_code, sedes=List((type(rlp_obj), type(rlp_obj))), recursive_cache=True
    )
    assert L2[0]._cached_rlp == rlp_obj_code
    assert L2[1]._cached_rlp == rlp_obj_code


def test_serializable_basic_copy(type_1_a):
    n_type_1_a = type_1_a.copy()
    assert n_type_1_a == type_1_a
    assert n_type_1_a is not type_1_a


def test_serializable_copy_with_nested_serializables(type_2):
    n_type_2 = type_2.copy()
    assert n_type_2 == type_2
    assert n_type_2 is not type_2

    assert n_type_2.field2_1 == type_2.field2_1
    assert n_type_2.field2_1 is not type_2.field2_1

    assert n_type_2.field2_2 == type_2.field2_2
    assert all(left == right for left, right in zip(n_type_2.field2_2, type_2.field2_2))
    assert all(
        left is not right for left, right in zip(n_type_2.field2_2, type_2.field2_2)
    )


def test_serializable_build_changeset(type_1_a):
    with type_1_a.build_changeset() as changeset:
        # make changes to copy
        changeset.field1 = 1234
        changeset.field2 = b"arst"

        # check that the copy has the new field values
        assert changeset.field1 == 1234
        assert changeset.field2 == b"arst"

        n_type_1_a = changeset.commit()

    # check that the copy has the new field values
    assert n_type_1_a.field1 == 1234
    assert n_type_1_a.field2 == b"arst"

    # ensure the base object hasn't changed.
    assert type_1_a.field1 == 5
    assert type_1_a.field2 == b"a"


def test_serializable_build_changeset_changeset_gets_decomissioned(type_1_a):
    with type_1_a.build_changeset() as changeset:
        changeset.field1 = 54321
        n_type_1_a = changeset.commit()

    # ensure that we also can't update the changeset
    with pytest.raises(AttributeError):
        changeset.field1 = 12345
    # ensure that we also can't read values from the changeset
    with pytest.raises(AttributeError):
        changeset.field1

    assert n_type_1_a.field1 == 54321


def test_serializable_build_changeset_with_params(type_1_a):
    with type_1_a.build_changeset(1234) as changeset:
        assert changeset.field1 == 1234

        n_type_1_a = changeset.commit()
    assert n_type_1_a.field1 == 1234


def test_serializable_build_changeset_using_open_close_api(type_1_a):
    changeset = type_1_a.build_changeset()
    changeset.open()

    # make changes to copy
    changeset.field1 = 1234
    changeset.field2 = b"arst"

    # check that the copy has the new field values
    assert changeset.field1 == 1234
    assert changeset.field2 == b"arst"

    n_type_1_a = changeset.build_rlp()

    # check that the copy has the new field values
    assert n_type_1_a.field1 == 1234
    assert n_type_1_a.field2 == b"arst"

    # ensure the base object hasn't changed.
    assert type_1_a.field1 == 5
    assert type_1_a.field2 == b"a"

    # check we can still access the unclosed changeset
    assert changeset.field1 == 1234

    changeset.close()

    with pytest.raises(AttributeError):
        assert changeset.field1 == 1234


def test_serializable_with_duplicate_field_names_is_error():
    msg1 = "duplicated in the `fields` declaration: field_a"
    with pytest.raises(TypeError, match=msg1):

        class ParentA(Serializable):
            fields = (
                ("field_a", big_endian_int),
                ("field_c", big_endian_int),
                ("field_d", big_endian_int),
                ("field_a", big_endian_int),
            )

    msg2 = "duplicated in the `fields` declaration: field_a,field_c"
    with pytest.raises(TypeError, match=msg2):

        class ParentB(Serializable):
            fields = (
                ("field_a", big_endian_int),
                ("field_c", big_endian_int),
                ("field_d", big_endian_int),
                ("field_a", big_endian_int),
                ("field_c", big_endian_int),
            )


def test_serializable_inheritance_enforces_inclusion_of_parent_fields():
    class Parent(Serializable):
        fields = (
            ("field_a", big_endian_int),
            ("field_b", big_endian_int),
            ("field_c", big_endian_int),
            ("field_d", big_endian_int),
        )

    with pytest.raises(TypeError, match="field_a,field_c"):

        class Child(Parent):
            fields = (
                ("field_b", big_endian_int),
                ("field_d", big_endian_int),
            )


def test_serializable_single_inheritance_with_no_fields():
    class Parent(Serializable):
        fields = (
            ("field_a", big_endian_int),
            ("field_b", big_endian_int),
        )

    class Child(Parent):
        pass

    parent = Parent(1, 2)
    assert parent.field_a == 1
    assert parent.field_b == 2
    assert Parent.serialize(parent) == [b"\x01", b"\x02"]

    child = Child(3, 4)
    assert child.field_a == 3
    assert child.field_b == 4
    assert Child.serialize(child) == [b"\x03", b"\x04"]


def test_serializable_single_inheritance_with_fields():
    class Parent(Serializable):
        fields = (
            ("field_a", big_endian_int),
            ("field_b", big_endian_int),
        )

    class Child(Parent):
        fields = (
            ("field_a", big_endian_int),
            ("field_b", big_endian_int),
            ("field_c", big_endian_int),
        )

    parent = Parent(1, 2)
    assert parent.field_a == 1
    assert parent.field_b == 2
    assert Parent.serialize(parent) == [b"\x01", b"\x02"]

    with pytest.raises(TypeError):
        # ensure that the fields don't somehow leak into the parent class.
        Parent(1, 2, 3)

    child = Child(3, 4, 5)
    assert child.field_a == 3
    assert child.field_b == 4
    assert child.field_c == 5
    assert Child.serialize(child) == [b"\x03", b"\x04", b"\x05"]


def test_serializable_inheritance_with_sedes_overrides():
    class Parent(Serializable):
        fields = (
            ("field_a", big_endian_int),
            ("field_b", big_endian_int),
        )

    class Child(Parent):
        fields = (
            ("field_a", binary),
            ("field_b", binary),
            ("field_c", binary),
        )

    parent = Parent(1, 2)
    assert parent.field_a == 1
    assert parent.field_b == 2
    assert Parent.serialize(parent) == [b"\x01", b"\x02"]

    child = Child(b"1", b"2", b"3")
    assert child.field_a == b"1"
    assert child.field_b == b"2"
    assert child.field_c == b"3"
    assert Child.serialize(child) == [b"1", b"2", b"3"]


def test_serializable_multiple_inheritance_without_fields_declaration_is_error():
    class ParentA(Serializable):
        fields = (("field_a", big_endian_int),)

    class ParentB(Serializable):
        fields = (("field_b", big_endian_int),)

    with pytest.raises(TypeError, match="explicit `fields` declaration"):

        class Child(ParentA, ParentB):
            pass


def test_serializable_multiple_inheritance_allowed_with_explicit_fields():
    class ParentA(Serializable):
        fields = (("field_a", big_endian_int),)

    class ParentB(Serializable):
        fields = (("field_b", big_endian_int),)

    # with same fields
    class ChildA(ParentA, ParentB):
        fields = (
            ("field_a", big_endian_int),
            ("field_b", big_endian_int),
        )

    # with extra fields
    class ChildB(ParentA, ParentB):
        fields = (
            ("field_a", big_endian_int),
            ("field_b", big_endian_int),
            ("field_c", big_endian_int),
        )


def test_serializable_multiple_inheritance_requires_all_parent_fields():
    class ParentA(Serializable):
        fields = (("field_a", big_endian_int),)

    class ParentB(Serializable):
        fields = (("field_b", big_endian_int),)

    with pytest.raises(TypeError, match="The following fields are missing: field_b"):

        class ChildA(ParentA, ParentB):
            fields = (("field_a", big_endian_int),)

    with pytest.raises(TypeError, match="The following fields are missing: field_a"):

        class ChildB(ParentA, ParentB):
            fields = (("field_b", big_endian_int),)

    with pytest.raises(
        TypeError, match="The following fields are missing: field_a,field_b"
    ):

        class ChildC(ParentA, ParentB):
            fields = (
                ("field_c", big_endian_int),
                ("field_d", big_endian_int),
            )


@pytest.mark.parametrize(
    "name",
    (
        "0_starts_with_digit",
        " starts_with_space",
        "$starts_with_dollar",
        "has_dollar_$_inside",
        "has spaces",
    ),
)
def test_serializable_field_names_must_be_valid_identifiers(name):
    with pytest.raises(
        TypeError, match=f"not valid python identifiers: `{re.escape(name)}`"
    ):

        class Klass(Serializable):
            fields = ((name, big_endian_int),)


def test_serializable_inheritance_from_base_with_no_fields():
    """
    ensure that we can create base classes of the base `Serializable` without
    declaring fields.
    """

    class ExtendedSerializable(Serializable):
        pass

    class FurtherExtendedSerializable(ExtendedSerializable):
        pass
