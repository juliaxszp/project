from src.ASCON.iv import ASCON128_IV
from src.ASCON.utils import int_to_bits
from src.ASCON.permutation import p12

def create_initial_state(key, nonce):

    iv = int_to_bits(ASCON128_IV, 64)

    state_bits = iv + key + nonce

    state = []

    for word in range(5):
        start = word * 64
        end = start + 64
        state.append(state_bits[start:end])

    return state


def initialization(Builder, key, nonce):

    state = create_initial_state(key, nonce)

    state = p12(Builder, state)

    state = xor_key(Builder, state, key)

    return state



def xor_key(Builder, state, key):

    for i in range(128):
        word = 3 + i // 64
        bit = i % 64

        out = Builder.var(f"init_key_xor_{word}_{bit}")

        Builder.xor([
            out,
            state[word][bit],
            key[i]
        ])

        state[word][bit] = out

    return state














from src.ASCON.iv import ASCON128_IV
from src.ASCON.utils import int_to_bits
from src.ASCON.permutation import p12
from src.ASCON.constants import get_const_zero, get_const_one

def create_initial_state(key, nonce, Builder=None):
    iv_raw = int_to_bits(ASCON128_IV, 64)


    iv_sat = []
    for bit in iv_raw:
        if bit == 1:
            iv_sat.append(get_const_one(Builder) if Builder is not None else 1)
        else:
            iv_sat.append(get_const_zero(Builder) if Builder is not None else 0)

    state_bits = iv_sat + key + nonce

    state = []

    for word in range(5):
        start = word * 64
        end = start + 64
        state.append(state_bits[start:end])

    return state


def xor_key_init(Builder, state, key, prefix="init_key_xor"):
    # W inicjalizacji klucz dodajemy do słów x3 i x4 (ostatnie 128 bitów stanu)
    for i in range(128):
        word = 3 + i // 64
        bit = i % 64

        out = Builder.var(f"{prefix}_S{word}_{bit}")

        Builder.xor([
            out,
            state[word][bit],
            key[i]
        ])

        state[word][bit] = out

    return state


def initialization(Builder, key, nonce):
    state = create_initial_state(key, nonce, Builder=Builder)

    # Permutacja 12 rund dla inicjalizacji z unikalnym prefixem
    state = p12(Builder, state, prefix="init_p12_")

    state = xor_key_init(Builder, state, key, prefix="init_key_xor")

    return state