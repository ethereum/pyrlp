import pytest
from rlp import SerializationError, utils
from rlp.sedes import big_endian_int, BigEndianInt

valid_data = (
    (256, b'\x01\x00'),
    (1024, b'\x04\x00'),
    (65535, b'\xff\xff'),
)

single_bytes = ((n, utils.ascii_chr(n)) for n in range(1, 256))

random_integers = (256, 257, 4839, 849302, 483290432, 483290483290482039482039,
                   48930248348219540325894323584235894327865439258743754893066)

negative_ints = (-1, -100, -255, -256, -2342423)


def test_neg():
    for n in negative_ints:
        with pytest.raises(SerializationError):
            big_endian_int.serialize(n)


def test_serialization():
    for n in random_integers:
        serial = big_endian_int.serialize(n)
        deserialized = big_endian_int.deserialize(serial)
        assert deserialized == n
        if n != 0:
            assert serial[0] != b'\x00'  # is not checked


def test_single_byte():
    for n, s in single_bytes:
        serial = big_endian_int.serialize(n)
        assert serial == s
        deserialized = big_endian_int.deserialize(serial)
        assert deserialized == n


def test_valid_data():
    for n, serial in valid_data:
        serialized = big_endian_int.serialize(n)
        deserialized = big_endian_int.deserialize(serial)
        assert serialized == serial
        assert deserialized == n


def test_fixedlength():
    s = BigEndianInt(4)
    for i in (0, 1, 255, 256, 256**3, 256**4 - 1):
        assert len(s.serialize(i)) == 4
        assert s.deserialize(s.serialize(i)) == i
    for i in (256**4, 256**4 + 1, 256**5, -1, -256, 'asdf'):
        with pytest.raises(SerializationError):
            s.serialize(i)
