import pytest
from rlp import encode, decode, SerializationError
from rlp.sedes import raw


serializable = (
    '',
    'asdf',
    'fds89032#$@%',
    b'',
    b'dfsa',
    ['dfsa', ''],
    [],
    ['fdsa', ['dfs', ['jfdkl']]],
)


not_serializable = (
    0,
    32,
    ['asdf', ['fdsa', [5]]],
    str
)


def test_serializable():
    for s in serializable:
        raw.serialize(s)
        code = encode(s, raw)
        assert s == decode(code, raw)
    for s in not_serializable:
        with pytest.raises(SerializationError):
            raw.serialize(s)
