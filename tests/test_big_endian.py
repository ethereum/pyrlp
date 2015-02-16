import pytest
from rlp import SerializationError, DeserializationError
from rlp.sedes.big_endian_int import serializable, serialize, deserialize


valid_data = (
    (256, '\x01\x00'),
    (1024, '\x04\x00'),
    (65535, '\xff\xff'),
)

single_bytes = ((n, chr(n)) for n in xrange(256))

random_integers = (256, 257, 4839, 849302, 483290432, 483290483290482039482039,
                   48930248348219540325894323584235894327865439258743754893066)

invalid_rlp = ('', '\x00\xab', '\x00\x00\xff')

negative_ints = (-1, -100, -255, -256, -2342423)


def test_neg():
    for n in negative_ints:
        assert not serializable(n)


def test_serialization():
    for n in random_integers:
        assert serializable(n)
        serial = serialize(n)
        deserialized = deserialize(serial)
        assert deserialized == n
        if n != 0:
            assert serial[0] != '\x00'  # is not checked


def test_single_byte():
    for n, s in single_bytes:
        serial = serialize(n)
        assert serial == s
        deserialized = deserialize(serial)
        assert deserialized == n


def test_valid_data():
    for n, serial in valid_data:
        serialized = serialize(n)
        deserialized = deserialize(serial)
        assert serialized == serial
        assert deserialized == n

def test_invalid_rlp():
    for serial in invalid_rlp:
        with pytest.raises(DeserializationError):
            deserialize(serial)
