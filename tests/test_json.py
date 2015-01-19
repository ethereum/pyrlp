import json
from collections import Sequence
import pytest
from rlp import encode, decode, infer_sedes
from rlp.sedes import sedes_list


with open('tests/rlptest.json') as f:
    test_data = json.loads(f.read())
    test_pieces = [(name, in_out) for name, in_out in test_data.iteritems()]


@pytest.mark.parametrize('name, in_out', test_pieces)
def test_encode(name, in_out):
    msg_format = 'Test {} failed (encoded {} to {} instead of {})'
    data = in_out['in']
    result = encode(data).encode('hex').upper()
    expected = in_out['out'].upper()
    if result != expected:
        pytest.fail(msg_format.format(name, data, result, expected))


@pytest.mark.parametrize('name, in_out', test_pieces)
def test_decode(name, in_out):
    msg_format = 'Test {} failed (decoded {} to {} instead of {})'
    rlp_string = in_out['out'].decode('hex')
    decoded = decode(rlp_string)
    expected = in_out['in']
    sedes = infer_sedes(expected, sedes_list)
    data = sedes.deserialize(decoded)
    if data != expected:
        pytest.fail(msg_format.format(name, rlp_string, decoded, expected))
