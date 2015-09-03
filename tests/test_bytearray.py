import rlp


def test_bytearray():
    e = rlp.encode('abc')
    d = rlp.decode(e)
    d = rlp.decode(bytearray(e))
