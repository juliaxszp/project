from src.ascon import BasicFunctions
from src.ASCON.finalization import *
from src.ASCON.key import create_key
from src.ASCON.state import create_state


def test_xor_key_into_state():
    builder = BasicFunctions()

    state = create_state(builder)
    key = create_key(builder)

    output = xor_key_into_state(
        builder,
        state,
        key
    )

    assert len(output) == 5

    for word in output:
        assert len(word) == 64


def test_finalization():
    builder = BasicFunctions()

    state = create_state(builder)
    key = create_key(builder)

    output = finalization(
        builder,
        state,
        key
    )

    assert len(output) == 5

    for word in output:
        assert len(word) == 64


def test_extract_tag():
    builder = BasicFunctions()

    state = create_state(builder)

    tag = extract_tag(state)

    assert len(tag) == 128