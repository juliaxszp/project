from src.ascon import BasicFunctions
from src.ASCON.associated_data import *
from src.ASCON.state import create_state
from src.ASCON.utils import int_to_bits




def test_create_associated_data():
    builder = BasicFunctions()

    ad = create_associated_data(builder, 128)

    assert len(ad) == 128




def test_split_into_blocks():
    bits = list(range(128))

    blocks = split_into_blocks(bits, 64)

    assert len(blocks) == 2
    assert len(blocks[0]) == 64
    assert len(blocks[1]) == 64


def test_xor_ad_block():
    builder = BasicFunctions()

    state = create_state(builder)
    ad = create_associated_data(builder, 64)

    output = xor_ad_block(builder, state, ad)

    assert len(output) == 5

    for word in output:
        assert len(word) == 64



def test_process_ad_block():
    builder = BasicFunctions()

    state = create_state(builder)
    ad = create_associated_data(builder, 64)

    output = process_ad_block(
        builder,
        state,
        ad
    )

    assert len(output) == 5

    for word in output:
        assert len(word) == 64


def test_process_associated_data():
    builder = BasicFunctions()

    state = create_state(builder)
    ad = create_associated_data(builder, 128)

    output = process_associated_data(
        builder,
        state,
        ad
    )

    assert len(output) == 5

    for word in output:
        assert len(word) == 64



def test_pad_block():
    block = [0] * 60

    padded = pad_block(block)

    assert len(padded) == 64
    assert padded[60] == 1

    for bit in padded[61:]:
        assert bit == 0




def test_domain_separation():
    builder = BasicFunctions()

    state = create_state(builder)

    output = domain_separation(
        builder,
        state
    )

    assert len(output) == 5

    for word in output:
        assert len(word) == 64




def test_associated_data_phase():
    builder = BasicFunctions()

    state = create_state(builder)
    ad = create_associated_data(builder, 128)

    output = associated_data_phase(
        builder,
        state,
        ad
    )

    assert len(output) == 5

    for word in output:
        assert len(word) == 64




def test_bit_order():
    builder = BasicFunctions()

    state = create_state(builder)

    state[4][63] = 1

    assert state[4][63] == 1
    assert state[4][0] != state[4][63]


def test_int_to_bits_bit_order():
    bits = int_to_bits(1, 64)

    assert bits[0] == 1
    assert bits[1] == 0
    assert bits[63] == 0