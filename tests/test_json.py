import json
import sys
import pytest
import rlp
from rlp import encode, decode, decode_lazy, infer_sedes, utils, DecodingError


if sys.version_info.major == 2:
    str_types = (str, unicode)
elif sys.version_info.major == 3:
    str_types = bytes
else:
    assert False


def evaluate(ll):
    if isinstance(ll, rlp.lazy.LazyList):
        return [evaluate(e) for e in ll]
    else:
        return ll


def to_bytes(value):
    if isinstance(value, str):
        return utils.str_to_bytes(value)
    elif isinstance(value, list):
        return [to_bytes(v) for v in value]
    else:
        return value


def compare_nested(got, expected):
    if isinstance(got, str_types):
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

with open('tests/rlptest.json') as f:
    test_data = json.loads(f.read())
    test_pieces = [(name, {'in': to_bytes(in_out['in']),
                           'out': utils.str_to_bytes(in_out['out'])})
                   for name, in_out in test_data.items()]


@pytest.mark.parametrize('name, in_out', test_pieces)
def test_encode(name, in_out):
    msg_format = 'Test {} failed (encoded {} to {} instead of {})'
    data = in_out['in']
    result = utils.encode_hex(encode(data)).upper()
    expected = in_out['out'].upper()
    if result != expected:
        pytest.fail(msg_format.format(name, data, result, expected))


@pytest.mark.parametrize('name, in_out', test_pieces)
def test_decode(name, in_out):
    msg_format = 'Test {} failed (decoded {} to {} instead of {})'
    rlp_string = utils.decode_hex(in_out['out'])
    decoded = decode(rlp_string)
    with pytest.raises(DecodingError):
        decode(rlp_string + b'\x00')
    assert decoded == decode(rlp_string + b'\x00', strict=False)

    assert decoded == evaluate(decode_lazy(rlp_string))
    expected = in_out['in']
    sedes = infer_sedes(expected)
    data = sedes.deserialize(decoded)
    assert compare_nested(data, decode(rlp_string, sedes))

    if not compare_nested(data, expected):
        pytest.fail(msg_format.format(name, rlp_string, decoded, expected))
