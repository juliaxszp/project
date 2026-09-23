from src.ASCON.state import create_state
from src.ascon import BasicFunctions


def test_create_state():

    builder = BasicFunctions()

    state = create_state(builder)

    assert len(state) == 5

    for word in state:
        assert len(word) == 64