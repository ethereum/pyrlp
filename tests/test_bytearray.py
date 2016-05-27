import rlp


def test_bytearray():
    e = rlp.encode('abc')
    d = rlp.decode(e)
    d = rlp.decode(bytearray(e))


def test_bytearray_lazy():
    e = rlp.encode('abc')
    d = rlp.decode(e)
    d = rlp.decode_lazy(bytearray(e))
