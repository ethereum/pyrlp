from rlp.sedes import FixedLengthInt


def test_fixedlengthint():
    s = FixedLengthInt(4)
    for i in (0, 1, 255, 256, 256**3, 256**4 - 1):
        assert s.serializable(i)
        assert len(s.serialize(i)) == 4
        assert s.deserialize(s.serialize(i)) == i
    for i in (256**4, 256**4 + 1, 256**5, -1, -256, 'asdf'):
        assert not s.serializable(i)
