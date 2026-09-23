from src.ASCON.key import create_key
from src.ASCON.nonce import create_nonce
from src.ASCON.initialization import create_initial_state
from src.ascon import BasicFunctions
from src.ASCON.iv import ASCON128_IV
from src.ASCON.utils import int_to_bits
from src.ASCON.initialization import create_initial_state, initialization
from src.ASCON.initialization import xor_key
from src.ASCON.permutation import p12 
from src.ASCON.utils import int_to_bits


def test_create_initial_state():
    builder = BasicFunctions()

    key = create_key(builder)
    nonce = create_nonce(builder)

    state = create_initial_state(key, nonce)

    assert len(state) == 5

    for word in state:
        assert len(word) == 64


def test_initial_state_contains_iv():
    builder = BasicFunctions()

    key = create_key(builder)
    nonce = create_nonce(builder)

    state = create_initial_state(key, nonce)

    expected_iv = int_to_bits(ASCON128_IV, 64)

    assert state[0] == expected_iv



def test_initialization():
    builder = BasicFunctions()

    key = create_key(builder)
    nonce = create_nonce(builder)

    state = initialization(builder, key, nonce)

    assert len(state) == 5

    for word in state:
        assert len(word) == 64



def test_xor_key():
    builder = BasicFunctions()

    key = create_key(builder)
    nonce = create_nonce(builder)

    state = create_initial_state(key, nonce)

    state = p12(builder, state)

    output = xor_key(builder, state, key)

    assert len(output) == 5

    for word in output:
        assert len(word) == 64



def test_initial_state_bit_layout():
    builder = BasicFunctions()

    key = int_to_bits(0x000102030405060708090A0B0C0D0E0F, 128)
    nonce = int_to_bits(0x000102030405060708090A0B0C0D0E0F, 128)

    state = create_initial_state(key, nonce)

    assert state[0] == int_to_bits(ASCON128_IV, 64)
    assert state[1] == key[:64]
    assert state[2] == key[64:]
    assert state[3] == nonce[:64]
    assert state[4] == nonce[64:]