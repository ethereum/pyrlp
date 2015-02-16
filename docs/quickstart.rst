Quickstart
==========

::

    >>> import rlp
    >>> from rlp.sedes import big_endian_int, text, ListSedes

::

    >>> rlp.encode(1234)
    '\x82\x04\xd2'
    >>> rlp.decode('\x82\x04\xd2', big_endian_int)

::

    >>> rlp.encode([1, [2, []]])
    '\xc4\x01\xc2\x02\xc0'
    '\xc5\x01\xc3\x02\xc1\x03'
    >>> list_sedes = ListSedes([big_endian_int, [big_endian_int, []]])
    >>> rlp.decode('\xc4\x01\xc2\x02\xc0', list_sedes)
    [1, [2, []]]

::

    >>> class Tx(rlp.Serializable):
    ...     fields = [
    ...         ('from', text),
    ...         ('to', text),
    ...         ('amount', big_endian_int)
    ...     ]
    ...
    >>> tx = Tx('me', 'you', 255)
    >>> rlp.encode(tx)
    '\xc9\x82me\x83you\x81\xff'
    >>> rlp.decode('\xc9\x82me\x83you\x81\xff', Tx) == tx
    True
