from src.ascon import BasicFunctions
from src.ASCON.plaintext import *
from src.ASCON.state import create_state


def test_create_plaintext():
    builder = BasicFunctions()

    plaintext = create_plaintext(builder, 128)

    assert len(plaintext) == 128


def test_split_into_blocks():
    plaintext = list(range(128))

    blocks = split_into_blocks(plaintext, 64)

    assert len(blocks) == 2
    assert len(blocks[0]) == 64
    assert len(blocks[1]) == 64


def test_xor_plaintext_block():
    builder = BasicFunctions()

    state = create_state(builder)
    plaintext = create_plaintext(builder, 64)

    output = xor_plaintext_block(
        builder,
        state,
        plaintext
    )

    assert len(output) == 64


def test_process_plaintext_block():
    builder = BasicFunctions()

    state = create_state(builder)
    plaintext = create_plaintext(builder, 64)

    output_state, ciphertext = process_plaintext_block(
        builder,
        state,
        plaintext
    )

    assert len(output_state) == 5

    for word in output_state:
        assert len(word) == 64

    assert len(ciphertext) == 64


def test_pad_block():
    block = [0] * 60

    padded = pad_block(block)

    assert len(padded) == 64
    assert padded[60] == 1

    for bit in padded[61:]:
        assert bit == 0


def test_process_plaintext_empty():
    builder = BasicFunctions()

    state = create_state(builder)

    output_state, ciphertext = process_plaintext(
        builder,
        state,
        []
    )

    assert len(output_state) == 5
    assert ciphertext == []


def test_process_plaintext_full_block():
    builder = BasicFunctions()

    state = create_state(builder)
    plaintext = create_plaintext(builder, 64)

    output_state, ciphertext = process_plaintext(
        builder,
        state,
        plaintext
    )

    assert len(output_state) == 5
    assert len(ciphertext) == 64


def test_process_plaintext_two_blocks():
    builder = BasicFunctions()

    state = create_state(builder)
    plaintext = create_plaintext(builder, 128)

    output_state, ciphertext = process_plaintext(
        builder,
        state,
        plaintext
    )

    assert len(output_state) == 5
    assert len(ciphertext) == 128


def test_process_plaintext_partial_block():
    builder = BasicFunctions()

    state = create_state(builder)
    plaintext = create_plaintext(builder, 100)

    output_state, ciphertext = process_plaintext(
        builder,
        state,
        plaintext
    )

    assert len(output_state) == 5
    assert len(ciphertext) == 100