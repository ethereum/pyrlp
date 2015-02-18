from rlp.sedes import BinarySedes


def test_binary():
    b1 = BinarySedes()
    for d in ('', 'asdf', '\x00' * 20, bytearray('fdsa')):
        assert b1.serializable(d)
        assert b1.serialize(d) == str(d)
    for d in ([], 5, str):
        assert not b1.serializable(d)

    b2 = BinarySedes.fixed_length(5)
    for d in ('asdfg', '\x00\x01\x02\x03\x04', bytearray('ababa')):
        assert b2.serializable(d)
        assert b2.serialize(d) == str(d)
    for d in ('asdf', 'asdfgh', '', 'bababa'):
        assert not b2.serializable(d)

    b3 = BinarySedes(2, 4)
    for d in ('as', 'dfg', 'hjkl', '\x00\x01\x02'):
        assert b3.serializable(d)
        assert b3.serialize(d) == str(d)
    for d in ('', 'a', 'abcde'):
        assert not b3.serializable(d)

    b4 = BinarySedes(min_length=3)
    for d in ('abc', 'abcd', 'x' * 132):
        assert b4.serializable(d)
        assert b4.serialize(d) == str(d)
    for d in ('ab', '', 'a', 'xy'):
        assert not b4.serializable(d)

    b5 = BinarySedes(max_length=3)
    for d in ('', 'ab', 'abc'):
        assert b5.serializable(d)
        assert b5.serialize(d) == str(d)
    for d in ('abcd', 'vwxyz', 'a' * 32):
        assert not b5.serializable(d)
