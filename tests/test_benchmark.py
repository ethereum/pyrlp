from itertools import repeat, chain
from random import randint
import sys
import pytest
import rlp
from rlp.sedes import binary, CountableList
from rlp.exceptions import DecodingError, DeserializationError


class Message(rlp.Serializable):

    fields = [
        ('field1', binary),
        ('field2', binary),
        ('field3', CountableList(binary, max_length=100))
    ]


SIZE = int(1e6)


def lazy_test_factory(s, valid):
    @pytest.mark.benchmark(group='lazy')
    def f(benchmark):
        @benchmark
        def result():
            try:
                Message.deserialize(rlp.decode_lazy(s))
            except (DecodingError, DeserializationError):
                return not valid
            else:
                return valid
        assert result
    return f


def eager_test_factory(s, valid):
    @pytest.mark.benchmark(group='eager')
    def f(benchmark):
        @benchmark
        def result():
            try:
                rlp.decode(s, Message)
            except (DecodingError, DeserializationError):
                return not valid
            else:
                return valid
        assert result
    return f


def generate_test_functions():
    valid = {}
    invalid = {}
    random_string = ''.join(chr(randint(0, 255)) for _ in repeat(None, SIZE))
    long_list = rlp.encode([c for c in random_string])
    invalid['long_string'] = random_string
    invalid['long_list'] = long_list

    nested_list = rlp.encode('\x00')
    for _ in repeat(None, SIZE):
        nested_list += rlp.codec.length_prefix(len(nested_list), 0xc0)
    invalid['nested_list'] = nested_list

    valid['long_string_object'] = rlp.encode(['\x00', random_string, []])

    prefix = rlp.codec.length_prefix(1 + 1 + len(long_list), 0xc0)
    invalid['long_list_object'] = prefix + rlp.encode('\x00') + rlp.encode('\x00') + long_list

    valid['friendly'] = rlp.encode(Message('hello', 'I\'m friendly', ['not', 'many', 'elements']))

    invalid = invalid.items()
    valid = valid.items()
    rlp_strings = [i[1] for i in chain(valid, invalid)]
    valids = [True] * len(valid) + [False] * len(invalid)
    names = [i[0] for i in chain(valid, invalid)]

    current_module = sys.modules[__name__]
    for rlp_string, valid, name in zip(rlp_strings, valids, names):
        f_eager = eager_test_factory(rlp_string, valid)
        f_lazy = lazy_test_factory(rlp_string, valid)
        setattr(current_module, 'test_eager_' + name, f_eager)
        setattr(current_module, 'test_lazy_' + name, f_lazy)


generate_test_functions()
