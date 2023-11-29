pyrlp v4.0.0 (2023-11-29)
-------------------------

Features
~~~~~~~~

- ``repr()`` now returns an evaluatable string, like ``MyRLPObj(my_int_field=1, my_str_field="a_str")`` (`#117 <https://github.com/ethereum/pyrlp/issues/117>`__)


Internal Changes - for pyrlp Contributors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Convert ``.format`` strings to ``f-strings`` (`#144 <https://github.com/ethereum/pyrlp/issues/144>`__)
- Add ``autoflake`` linting and move config to ``pyproject.toml`` (`#145 <https://github.com/ethereum/pyrlp/issues/145>`__)


Release Notes
=============

.. _v0.4.8-release-notes:

0.4.8
-----

- Implement ``Serializable.make_mutable`` and ``rlp.sedes.make_mutable`` API.
- Add ``mutable`` flag to ``Serializable.deserialize`` to allow deserialization into mutable objects.
