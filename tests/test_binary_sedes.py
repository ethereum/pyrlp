# -*- coding: UTF-8 -*-
import pytest
from rlp import SerializationError, utils
from rlp.sedes import Binary


def test_binary():
    b1 = Binary()
    f = {
        '': b'',
        'asdf': b'asdf',
        ('\x00' * 20): (b'\x00' * 20),
        'fdsa': b'fdsa'
    }
    for k in f:
        assert b1.serialize(k) == f[k]
    for d in ([], 5, str):
        with pytest.raises(SerializationError):
            b1.serialize(d)

    b2 = Binary.fixed_length(5)
    f = {
        'asdfg': b'asdfg',
        b'\x00\x01\x02\x03\x04': b'\x00\x01\x02\x03\x04',
        utils.str_to_bytes('ababa'): b'ababa'
    }
    for k in f:
        assert b2.serialize(k) == f[k]

    for d in ('asdf', 'asdfgh', '', 'bababa'):
        with pytest.raises(SerializationError):
            b2.serialize(d)

    b3 = Binary(2, 4)
    f = {
        'as': b'as',
        'dfg': b'dfg',
        'hjkl': b'hjkl',
        b'\x00\x01\x02': b'\x00\x01\x02'
    }
    for k in f:
        assert b3.serialize(k) == f[k]
    for d in ('', 'a', 'abcde', 'äää'):
        with pytest.raises(SerializationError):
            b3.serialize(d)

    b4 = Binary(min_length=3)
    f = {'abc': b'abc', 'abcd': b'abcd', ('x' * 132): (b'x' * 132)}
    for k in f:
        assert b4.serialize(k) == f[k]
    for d in ('ab', '', 'a', 'xy'):
        with pytest.raises(SerializationError):
            b4.serialize(d)

    b5 = Binary(max_length=3)
    f = {'': b'', 'ab': b'ab', 'abc': b'abc'}
    for k in f:
        assert b5.serialize(k) == f[k]
    for d in ('abcd', 'vwxyz', 'a' * 32):
        with pytest.raises(SerializationError):
            b5.serialize(d)

    b6 = Binary(min_length=3, max_length=5, allow_empty=True)
    f = {'': b'', 'abc': b'abc', 'abcd': b'abcd', 'abcde': b'abcde'}
    for k in f:
        assert b6.serialize(k) == f[k]
    for d in ('a', 'ab', 'abcdef', 'abcdefgh' * 10):
        with pytest.raises(SerializationError):
            b6.serialize(d)
