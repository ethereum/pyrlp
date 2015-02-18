.. _api-reference:

API Reference
=============

Functions
---------

.. autofunction:: rlp.encode

.. autofunction:: rlp.decode

.. autofunction:: rlp.infer_sedes

Sedes Objects
-------------

.. data:: rlp.sedes.big_endian_int

   A sedes object for non negative integers using big endian notation.

.. data:: rlp.sedes.text

   A sedes object for textual data using UTF-8.

.. data:: rlp.sedes.raw

   A sedes that does nothing. Thus, it can serialize everything that can be
   directly encoded in RLP. This sedes can be used as a placeholder when
   deserializing larger structures.

.. data:: rlp.sedes.sedes_list

   A list of sedes objects that is passed to :func:`rlp.infer_sedes` by
   :func:`rlp.encode`. By default, this contains only
   :mod:`rlp.sedes.big_endian_int` and :mod:`rlp.sedes.text`, but can be
   extended.

.. autoclass:: rlp.sedes.BinarySedes

   .. automethod:: rlp.sedes.BinarySedes.fixed_length

.. autoclass:: rlp.sedes.FixedLengthInt

.. autoclass:: rlp.sedes.ListSedes

.. autoclass:: rlp.sedes.CountableListSedes

.. autoclass:: rlp.Serializable
    :members:

Exceptions
----------

.. autoexception:: rlp.RLPException

.. autoexception:: rlp.EncodingError

.. autoexception:: rlp.DecodingError

.. autoexception:: rlp.SerializationError

.. autoexception:: rlp.DeserializationError
