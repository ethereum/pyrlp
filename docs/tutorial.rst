Tutorial
========

Basics
------

There are two types of fundamental items one can encode in RLP:

    1) Strings of bytes
    2) Lists of other items

In this package, byte strings are represented either as Python strings or as
``bytearrays``. Lists can be any sequence, e.g. ``lists`` or ``tuples``. To
encode these kinds of objects, use :func:`rlp.encode`::

    >>> from rlp import encode
    >>> encode('ethereum')
    '\x88ethereum'
    >>> encode('')
    '\x80'
    >>> encode('Lorem ipsum dolor sit amet, consetetur sadipscing elitr.')
    '\xb88Lorem ipsum dolor sit amet, consetetur sadipscing elitr.'
    >>> encode([])
    '\xc0'
    >>> encode(['this', ['is', ('a', ('nested', 'list', []))]]) 
    '\xd9\x84this\xd3\x82is\xcfa\xcd\x86nested\x84list\xc0'


Decoding is just as simple::

    >>> from rlp import decode
    >>> decode('\x88ethereum')
    'ethereum'
    >>> decode('\x80')
    ''
    >>> decode('\xc0')
    []
    >>> decode('\xd9\x84this\xd3\x82is\xcfa\xcd\x86nested\x84list\xc0')
    ['this', ['is', ['a', ['nested', 'list', []]]]]


Now, what if we want to encode a different object, say, an integer? Let's try::

    >>> encode(1503)
    '\x82\x05\xdf'
    >>> decode('\x82\x05\xdf')
    '\x05\xdf'


Oops, what happened? Encoding worked fine, but :func:`rlp.decode` refused to
give an integer back. The reason is that RLP is typeless. It doesn't know if the
encoded data represents a number, a string, or a more complicated object. It
only distinguishes between byte strings and lists. Therefore, *pyrlp* guesses
how to serialize the object into a byte string (here, in big endian notation).
When encoded however, the type information is lost and :func:`rlp.decode`
returned the result in its most generic form, as a string. Thus, what we need
to do is deserialize the result afterwards.


Sedes objects
-------------

Serialization and its couterpart, deserialization, is done by, what we call,
*sedes objects* (borrowing from the word "codec"). For integers, the sedes
:mod:`rlp.sedes.big_endian_int` is in charge. To decode our integer, we can
pass this sedes to :func:`rlp.decode`::

    >>> from rlp.sedes import big_endian_int
    >>> decode('\x82\x05\xdf', big_endian_int)
    1503


For unicode strings, there's the sedes :mod:`rlp.sedes.text`, which uses UTF-8
to convert to and from byte strings::

    >>> from rlp.text import text
    >>> encode(u'Ðapp')
    '\x85\xc3\x90app'
    >>> decode('\x85\xc3\x90app', text)
    u'\xd0app'
    >>> print decode('\x85\xc3\x90app', text)
    Ðapp


Lists are a bit more difficult as they can contain arbitrarily complex
combinations of types. Therefore, we need to create a sedes object specific for
each list type. As base class for this we can use
:class:`rlp.sedes.ListSedes`::

    >>> from rlp.sedes import ListSedes
    >>> encode([5, 'fdsa', 0])
    '\xc7\x05\x84fdsa\x00'
    >>> sedes = ListSedes([big_endian_int, text, big_endian_int])
    >>> decode('\xc7\x05\x84fdsa\x00', sedes)
    [5, u'fdsa', 0]


Unsurprisingly, it is also possible to nest :class:`rlp.ListSedes` objects::

    >>> inner = ListSedes([text, text])
    >>> outer = ListSedes([inner, inner, inner])
    >>> decode(encode(['asdf', 'fdsa']), inner)
    [u'asdf', u'fdsa']
    >>> decode(encode([['a1', 'a2'], ['b1', 'b2'], ['c1', 'c2']]), outer)
    [[u'a1', u'a2'], [u'b1', u'b2'], [u'c1', u'c2']]


What Sedes Objects Actually Are
-------------------------------

We saw how to use sedes objects, but what exactly are they? They are
characterized by providing the following three member functions:

    - ``serializable(obj)``
    - ``serialize(obj)``
    - ``deserialize(serial)``

The latter two are used to convert between a Python object and its
representation as byte strings or sequences. The former one may be called by
:func:`rlp.encode` to infer which sedes object to use for a given object (see
:ref:`inference-section`).

For basic types, the sedes object is usually a module (e.g.
:mod:`rlp.sedes.big_endian_int` and :mod:`rlp.sedes.text`). Instances of
:class:`rlp.sedes.ListSedes` provide the sedes interface too, as well as the
class :class:`rlp.Serializable` which is discussed in the following section.


Encoding Custom Objects
-----------------------

Often, we want to encode our own objects in RLP. Examples from the Ethereum
world are transactions, blocks or anything send over the Wire. With *pyrlp*,
this is as easy as subclassing :class:`rlp.Serializable`::

    >>> import rlp
    >>> class Transaction(rlp.Serializable)
    ...    fields = (
    ...        ('sender', text),
    ...        ('receiver', text),
    ...        ('amount', big_endian_int)
    ...    )


The class attribute :attr:`~rlp.Serializable.fields` is a sequence of 2-tuples
defining the field names and the corresponding sedes. For each name an instance
attribute is created, that can conveniently be initialized with
:meth:`~rlp.Serializable.__init__`::

    >>> tx1 = Transaction('me', 'you', 255)
    >>> tx2 = Transaction(amount=255, sender='you', receiver='me')
    >>> tx1.amount
    255


At serialization, the field names are dropped and the object is converted to a
list, where the provided sedes objects are used to serialize the object
attributes::

    >>> Transaction.serialize(tx1)
    ['me', 'you', '\xff']
    >>> tx1 == Transaction.deserialize(['me', 'you', '\xff'])
    True
    >>> Transaction.serializable(tx1)
    True


As we can see, each subclass of :class:`rlp.Serializable` implements the sedes
responsible for its instances. Therefore, we can use :func:`rlp.encode` and
:func:`rlp.decode` as expected::

    >>> encode(tx1)
    '\xc9\x82me\x83you\x81\xff'
    >>> decode('\xc9\x82me\x83you\x81\xff', Transaction) == tx1
    True


.. _inference-section:

Sedes Inference
---------------

As we have seen, :func:`rlp.encode` (or, rather, :func:`rlp.infer_sedes`)
tries to guess a sedes capable of serializing the object before encoding. In
this process, it follows the following steps:

1) Check if the object's class is a sedes object (like every subclass of
   :class:`rlp.Serializable`). If so, its class is the sedes.
2) Check if one of the entries in :attr:`rlp.sedes.sedes_list` can serialize
   the object (via ``serializable(obj)``). If so, this is the sedes.
3) Check if the object is a sequence. If so, build a
   :class:`rlp.sedes.ListSedes` by recursively infering a sedes for each of its
   elements.
4) If none of these steps was successful, sedes inference has failed.

If you have build your own basic sedes (e.g. for ``dicts`` or ``floats``), you
might want to hook in at step 2 and add it to :attr:`rlp.sedes.sedes_list`,
whereby it will be automatically be used by :func:`rlp.encode`.


Further Reading
---------------

This was basically everything there is to about this package. The technical
specification of RLP can be found either in the
`Ethereum wiki <https://github.com/ethereum/wiki/wiki/RLP>`_ or in Appendix B of
Gavin Woods `Yellow Paper <http://gavwood.com/Paper.pdf>`_. For more detailed
information about this package, have a look at the :ref:`API-reference` or the
source code.
