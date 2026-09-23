from src.ascon import BasicFunctions
from src.ASCON.state import create_state
from src.ASCON.round import round_function


def test_round_structure():

    builder = BasicFunctions()

    state = create_state(builder)

    output = round_function(
        builder,
        state,
        0xF0
    )

    assert len(output) == 5

    for word in output:
        assert len(word) == 64



def test_rounds_use_different_variables():
    builder = BasicFunctions()

    state = create_state(builder)

    state_r0 = round_function(builder, state, 0xf0, round_number=0)
    state_r1 = round_function(builder, state_r0, 0xe1, round_number=1)

    assert state_r0 != state_r1