Release Notes
=============

Unreleased (latest source)
--------------------------

- `repr()` now returns an evaluatable string, like ``MyRLPObj(my_int_field=1, my_str_field="a_str")`` -
  `#117 <https://github.com/ethereum/pyrlp/pull/117>`_

.. _v0.4.8-release-notes:

0.4.8
-----

- Implement ``Serializable.make_mutable`` and ``rlp.sedes.make_mutable`` API.
- Add ``mutable`` flag to ``Serializable.deserialize`` to allow deserialization into mutable objects.
