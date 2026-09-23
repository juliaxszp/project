from src.ascon import BasicFunctions
from src.ASCON.key import create_key


def test_create_key():
    builder = BasicFunctions()

    key = create_key(builder)

    assert len(key) == 128