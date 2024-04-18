"""
util to benchmark known usecase
"""
import random
import time

import rlp
from rlp.sedes import (
    BigEndianInt,
    Binary,
    CountableList,
    big_endian_int,
    binary,
)
from rlp.sedes.serializable import (
    Serializable,
)

address = Binary.fixed_length(20, allow_empty=True)
int20 = BigEndianInt(20)
int32 = BigEndianInt(32)
int256 = BigEndianInt(256)
hash32 = Binary.fixed_length(32)
trie_root = Binary.fixed_length(32, allow_empty=True)


def zpad(x, length):
    return b"\x00" * max(0, length - len(x)) + x


class Transaction(Serializable):
    fields = [
        ("nonce", big_endian_int),
        ("gasprice", big_endian_int),
        ("startgas", big_endian_int),
        ("to", address),
        ("value", big_endian_int),
        ("data", binary),
        ("v", big_endian_int),
        ("r", big_endian_int),
        ("s", big_endian_int),
    ]

    def __init__(
        self, nonce, gasprice, startgas, to, value, data, v=0, r=0, s=0, **kwargs
    ):
        super().__init__(nonce, gasprice, startgas, to, value, data, v, r, s, **kwargs)


class BlockHeader(Serializable):
    fields = [
        ("prevhash", hash32),
        ("uncles_hash", hash32),
        ("coinbase", address),
        ("state_root", trie_root),
        ("tx_list_root", trie_root),
        ("receipts_root", trie_root),
        ("bloom", int256),
        ("difficulty", big_endian_int),
        ("number", big_endian_int),
        ("gas_limit", big_endian_int),
        ("gas_used", big_endian_int),
        ("timestamp", big_endian_int),
        ("extra_data", binary),
        ("mixhash", binary),
        ("nonce", binary),
    ]


class Block(Serializable):
    fields = [
        ("header", BlockHeader),
        ("transaction_list", CountableList(Transaction)),
        ("uncles", CountableList(BlockHeader)),
    ]

    def __init__(self, header, transaction_list=None, uncles=None, **kwargs):
        super().__init__(header, transaction_list or [], uncles or [], **kwargs)


def rand_bytes(num=32):
    return zpad(big_endian_int.serialize(random.getrandbits(num * 8)), num)


rand_bytes32 = rand_bytes


def rand_address():
    return rand_bytes(20)


def rand_bytes8():
    return rand_bytes(8)


def rand_bigint():
    return random.getrandbits(256)


def rand_int():
    return random.getrandbits(32)


rand_map = {
    hash32: rand_bytes32,
    trie_root: rand_bytes32,
    binary: rand_bytes32,
    address: rand_address,
    Binary: rand_bytes8,
    big_endian_int: rand_int,
    int256: rand_bigint,
}

assert Binary in rand_map


def mk_transaction():
    return Transaction(
        rand_int(),
        rand_int(),
        rand_int(),
        rand_address(),
        rand_int(),
        rand_bytes32(),
        27,
        rand_bigint(),
        rand_bigint(),
    )


rlp.decode(rlp.encode(mk_transaction()), Transaction)


def mk_block_header():
    return BlockHeader(*[rand_map[t]() for _, t in BlockHeader._meta.fields])


rlp.decode(rlp.encode(mk_block_header()), BlockHeader)


def mk_block(num_transactions=10, num_uncles=1):
    return Block(
        mk_block_header(),
        [mk_transaction() for _ in range(num_transactions)],
        [mk_block_header() for _ in range(num_uncles)],
    )


rlp.decode(rlp.encode(mk_block()), Block)


def do_test_serialize(block, rounds=100):
    for _ in range(rounds):
        x = rlp.encode(block, cache=False)
    return x


def do_test_deserialize(data, rounds=100, sedes=Block):
    for _ in range(rounds):
        x = rlp.decode(data, sedes)
    return x


def main(rounds=10000):
    st = time.time()
    d = do_test_serialize(mk_block(), rounds)
    elapsed = time.time() - st
    print("Block serializations / sec: %.2f" % (rounds / elapsed))

    st = time.time()
    d = do_test_deserialize(d, rounds)
    elapsed = time.time() - st
    print("Block deserializations / sec: %.2f" % (rounds / elapsed))

    st = time.time()
    d = do_test_serialize(mk_transaction(), rounds)
    elapsed = time.time() - st
    print("TX serializations / sec: %.2f" % (rounds / elapsed))

    st = time.time()
    d = do_test_deserialize(d, rounds, sedes=Transaction)
    elapsed = time.time() - st
    print("TX deserializations / sec: %.2f" % (rounds / elapsed))


if __name__ == "__main__":
    main()
    """
    py2
    serializations / sec: 658.64
    deserializations / sec: 1331.62

    pypy2
    serializations / sec: 4628.81      : x7 speedup
    deserializations / sec: 4753.84    : x3.5 speedup
    """
