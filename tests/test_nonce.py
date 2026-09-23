from src.ascon import BasicFunctions
from src.ASCON.nonce import create_nonce


def test_create_nonce():
    builder = BasicFunctions()

    nonce = create_nonce(builder)

    assert len(nonce) == 128