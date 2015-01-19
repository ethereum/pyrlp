import pytest
from collections import OrderedDict
from rlp import infer_sedes, Serializable, encode, decode
from rlp.sedes import big_endian_int, text, ListSedes, sedes_list


def test_inference():
    obj_sedes_pairs = (
        (5, big_endian_int),
        (0, big_endian_int),
        (-1, None),
        ('', text),
        ('asdf', text),
        (u'\xe4\xf6\xfc\xea\xe2\xfb', text),
        ([], ListSedes()),
        ([1, 2, 3], ListSedes((big_endian_int,) * 3)),
        ([[], 'asdf'], ListSedes((ListSedes(), text))),
    )

    for obj, sedes in obj_sedes_pairs:
        if sedes is not None:
            inferred = infer_sedes(obj, sedes_list)
            assert inferred == sedes
        else:
            with pytest.raises(TypeError):
                infer_sedes(obj)


def test_serializable():
    class Test1(Serializable):
        fields = (
            ('field1', big_endian_int),
            ('field2', text),
            ('field3', ListSedes((big_endian_int, text)))
        )
    class Test2(Serializable):
        fields = (
            ('field1', Test1),
            ('field2', ListSedes((Test1, Test1))),
        )
    t1a_data = (5, 'a', (0, ''))
    t1b_data = (9, 'b', (2, ''))
    test1a = Test1(*t1a_data)
    test1b = Test1(*t1b_data)
    test2 = Test2(test1a, [test1a, test1b])
    t2_data = (t1a_data, (t1a_data, t1b_data))

    # equality
    assert test1a == test1a
    assert test1b == test1b
    assert test2 == test2
    assert test1a != test1b
    assert test1b != test2
    assert test2 != test1a

    # serializable
    assert Test1.serializable(test1a) is True
    assert Test1.serializable(test1b) is True
    assert Test2.serializable(test2) is True
    assert Test1.serializable(test2) is False
    assert Test2.serializable(test1a) is False
    assert Test2.serializable(test1b) is False

    # inference
    assert infer_sedes(test1a, sedes_list) == Test1
    assert infer_sedes(test1b, sedes_list) == Test1
    assert infer_sedes(test2, sedes_list) == Test2

    # serialization
    serial_1a = Test1.serialize(test1a)
    serial_1b = Test1.serialize(test1b)
    serial_2 = Test2.serialize(test2)
    assert serial_1a == ['\x05', 'a', ['\x00', '']]
    assert serial_1b == ['\x09', 'b', ['\x02', '']]
    assert serial_2 == [serial_1a, [serial_1a, serial_1b]]

    # deserialization
    assert Test1.deserialize(serial_1a) == test1a
    assert Test1.deserialize(serial_1b) == test1b
    assert Test2.deserialize(serial_2) == test2

    # encoding and decoding
    assert decode(encode(test1a), Test1) == test1a
    assert decode(encode(test1b), Test1) == test1b
    assert decode(encode(test2), Test2) == test2
