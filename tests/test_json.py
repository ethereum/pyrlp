import json

from eth_utils import (
    add_0x_prefix,
    decode_hex,
    encode_hex,
)
import pytest

import rlp
from rlp import (
    DecodingError,
    decode,
    decode_lazy,
    encode,
    infer_sedes,
)


def evaluate(ll):
    if isinstance(ll, rlp.lazy.LazyList):
        return [evaluate(e) for e in ll]
    else:
        return ll


def normalize_input(value):
    if isinstance(value, str):
        return value.encode("utf8")
    elif isinstance(value, list):
        return [normalize_input(v) for v in value]
    elif isinstance(value, int):
        return value
    else:
        raise ValueError("Unsupported type")


def compare_nested(got, expected):
    if isinstance(got, bytes):
        return got == expected
    try:
        zipped = zip(got, expected)
    except TypeError:
        return got == expected
    else:
        if len(list(zipped)) == len(got) == len(expected):
            return all(compare_nested(x, y) for x, y in zipped)
        else:
            return False


with open("tests/rlptest.json") as rlptest_file:
    test_data = json.load(rlptest_file)
    test_pieces = [
        (
            name,
            {
                "in": normalize_input(in_out["in"]),
                "out": add_0x_prefix(in_out["out"]),
            },
        )
        for name, in_out in test_data.items()
    ]


@pytest.mark.parametrize("name, in_out", test_pieces)
def test_encode(name, in_out):
    data = in_out["in"]
    result = encode_hex(encode(data)).lower()
    expected = in_out["out"].lower()
    if result != expected:
        pytest.fail(
            f"Test {name} failed (encoded {data} to {result} instead of {expected})"
        )


@pytest.mark.parametrize("name, in_out", test_pieces)
def test_decode(name, in_out):
    rlp_string = decode_hex(in_out["out"])
    decoded = decode(rlp_string)
    with pytest.raises(DecodingError):
        decode(rlp_string + b"\x00")
    assert decoded == decode(rlp_string + b"\x00", strict=False)

    assert decoded == evaluate(decode_lazy(rlp_string))
    expected = in_out["in"]
    sedes = infer_sedes(expected)
    data = sedes.deserialize(decoded)
    assert compare_nested(data, decode(rlp_string, sedes))

    if not compare_nested(data, expected):
        pytest.fail(
            f"Test {name} failed (decoded {rlp_string} to {decoded} instead of {expected})"  # noqa: E501
        )
