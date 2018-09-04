Quickstart
==========

::

    >>> import rlp
    >>> from rlp.sedes import big_endian_int, text, List

::

    >>> rlp.encode(1234)
    b'\x82\x04\xd2'
    >>> rlp.decode(b'\x82\x04\xd2', big_endian_int)
    1234

::

    >>> rlp.encode([1, [2, []]])
    b'\xc4\x01\xc2\x02\xc0'
    >>> list_sedes = List([big_endian_int, [big_endian_int, []]])
    >>> rlp.decode(b'\xc4\x01\xc2\x02\xc0', list_sedes)
    (1, (2, ()))

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
    b'\xc9\x82me\x83you\x81\xff'
    >>> rlp.decode(b'\xc9\x82me\x83you\x81\xff', Tx) == tx
    True
