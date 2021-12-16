# Sometimes elements of a Serializable might be arbitrarily byte-strings or lists.
# See: https://github.com/ethereum/pyrlp/issues/112#issuecomment-785326962

import rlp
from rlp.sedes import big_endian_int, binary, CountableList
from rlp.sedes.dynamic import DynamicSerializable
from rlp.sedes.serializable import Serializable


class LegacyTransaction(Serializable):
    fields = [
        ('nonce', big_endian_int),
        ('gasprice', big_endian_int),
        # ...snip
    ]


class TypedTransaction(DynamicSerializable):
    sedes_options = [
        LegacyTransaction,
        binary,  # New typed transactions are opaque bytes
    ]


class Block(Serializable):
    fields = [
        ('transaction_list', CountableList(TypedTransaction)),
    ]


class LegacyBlock(Serializable):
    fields = [
        ('transaction_list', CountableList(LegacyTransaction)),
    ]


def test_dynamic_internal_legacy():
    # Just establish that the basic test setup is working
    block = LegacyBlock([LegacyTransaction(1, 2)])
    assert block.transaction_list[0].nonce == 1
    assert block.transaction_list[0].gasprice == 2

    serialized = rlp.encode(block)
    assert serialized == b'\xc4\xc3\xc2\x01\x02'

    decoded_block = rlp.decode(serialized, sedes=LegacyBlock)
    assert decoded_block == block
    assert decoded_block.transaction_list[0].nonce == 1
    assert decoded_block.transaction_list[0].gasprice == 2


def test_dynamic_internal_list():
    block = Block([LegacyTransaction(1, 2)])
    assert block.transaction_list[0].nonce == 1
    assert block.transaction_list[0].gasprice == 2

    serialized = rlp.encode(block)
    assert serialized == b'\xc4\xc3\xc2\x01\x02'

    decoded_block = rlp.decode(serialized, sedes=Block)
    assert decoded_block == block
    assert decoded_block.transaction_list[0].nonce == 1
    assert decoded_block.transaction_list[0].gasprice == 2


def test_dynamic_internal_bytes():
    block = Block([b'\x01new-type'])
    assert block.transaction_list[0] == b'\x01new-type'

    serialized = rlp.encode(block)
    assert serialized == b'\xcb\xca\x89\x01new-type'

    decoded_block = rlp.decode(serialized, sedes=Block)
    assert decoded_block == block
    assert decoded_block.transaction_list[0] == b'\x01new-type'


def test_dynamic_internal_combined():
    block = Block([LegacyTransaction(1, 2), b'\x01new-type'])
    assert block.transaction_list[0].nonce == 1
    assert block.transaction_list[0].gasprice == 2
    assert block.transaction_list[1] == b'\x01new-type'

    serialized = rlp.encode(block)
    assert serialized == b'\xce\xcd\xc2\x01\x02\x89\x01new-type'

    decoded_block = rlp.decode(serialized, sedes=Block)
    assert decoded_block == block
    assert decoded_block.transaction_list[0].nonce == 1
    assert decoded_block.transaction_list[0].gasprice == 2
    assert decoded_block.transaction_list[1] == b'\x01new-type'
