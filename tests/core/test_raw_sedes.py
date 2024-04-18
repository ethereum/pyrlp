import pytest

from rlp import (
    DecodingError,
    SerializationError,
    decode,
    encode,
)
from rlp.sedes import (
    raw,
)

serializable = (
    b"",
    b"asdf",
    b"fds89032#$@%",
    b"",
    b"dfsa",
    [b"dfsa", b""],
    [],
    [b"fdsa", [b"dfs", [b"jfdkl"]]],
)


def test_serializable():
    for s in serializable:
        raw.serialize(s)
        code = encode(s, raw)
        assert s == decode(code, raw)


@pytest.mark.parametrize(
    "rlp_data",
    (0, 32, ["asdf", ["fdsa", [5]]], str),
)
def test_invalid_serializations(rlp_data):
    with pytest.raises(SerializationError):
        raw.serialize(rlp_data)


@pytest.mark.parametrize(
    "rlp_data",
    (
        None,
        "asdf",
    ),
)
def test_invalid_deserializations(rlp_data):
    with pytest.raises(DecodingError):
        decode(rlp_data, raw)
