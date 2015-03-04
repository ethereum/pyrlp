.. _api-reference:

API Reference
=============

Functions
---------

.. autofunction:: rlp.encode

.. autofunction:: rlp.decode

.. autofunction:: rlp.decode_lazy

    .. autoclass:: rlp.LazyList

.. autofunction:: rlp.infer_sedes


Sedes Objects
-------------

.. data:: rlp.sedes.raw

   A sedes object that does nothing. Thus, it can serialize everything that can
   be directly encoded in RLP (nested lists of strings). This sedes can be used
   as a placeholder when deserializing larger structures.

.. autoclass:: rlp.sedes.Binary

   .. automethod:: rlp.sedes.Binary.fixed_length

.. data:: rlp.sedes.binary

    A sedes object for binary data of arbitrary length (an instance of
    :class:`rlp.sedes.Binary` with default arguments).

.. autoclass:: rlp.sedes.BigEndianInt

.. data:: rlp.sedes.big_endian_int

    A sedes object for integers encoded in big endian without any leading zeros
    (an instance of :class:`rlp.sedes.BigEndianInt` with default arguments).

.. autoclass:: rlp.sedes.List

.. autoclass:: rlp.sedes.CountableList

.. autoclass:: rlp.Serializable
    :members:

Exceptions
----------

.. autoexception:: rlp.RLPException

.. autoexception:: rlp.EncodingError

.. autoexception:: rlp.DecodingError

.. autoexception:: rlp.SerializationError

.. autoexception:: rlp.DeserializationError
