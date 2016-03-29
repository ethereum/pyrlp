import rlp

def test_compare_length():
    data = rlp.encode([1,2,3,4,5])
    assert rlp.compare_length(data, 100) == -1
    assert rlp.compare_length(data, 5) == 0
    assert rlp.compare_length(data, 1) == 1

    data = rlp.encode([])
    assert rlp.compare_length(data, 100) == -1
    assert rlp.compare_length(data, 0) == 0
    assert rlp.compare_length(data, -1) == 1
