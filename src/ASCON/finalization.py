from src.ASCON.permutation import p12


def xor_key_into_state(Builder, state, key, prefix="final_key_xor"):
    for i in range(128):
        word = 3 + i // 64
        bit = i % 64

        out = Builder.var(
            f"{prefix}_S{word}_{bit}"
        )

        Builder.xor([
            out,
            state[word][bit],
            key[i]
        ])

        state[word][bit] = out

    return state


def finalization(Builder, state, key):
    state = xor_key_into_state(
        Builder,
        state,
        key,
        prefix="final_key_xor_1"
    )

    state = p12(
        Builder,
        state,
        prefix="final_p12_"
    )

    state = xor_key_into_state(
        Builder,
        state,
        key,
        prefix="final_key_xor_2"
    )

    return state


def extract_tag(state):
    tag = state[3] + state[4]
    return tag







from src.ASCON.permutation import p12


def xor_key_x1_x2(Builder, state, key, prefix="final_key_xor_1"):
    """Dodaje 128-bitowy klucz do słów x1 oraz x2 (przed p12)."""
    for i in range(128):
        word = 1 + i // 64  # Słowa x1 i x2
        bit = i % 64

        out = Builder.var(f"{prefix}_S{word}_{bit}")

        Builder.xor([
            out,
            state[word][bit],
            key[i]
        ])

        state[word][bit] = out

    return state


def xor_key_x3_x4(Builder, state, key, prefix="final_key_xor_2"):
    """Dodaje 128-bitowy klucz do słów x3 oraz x4 (po p12)."""
    for i in range(128):
        word = 3 + i // 64  # Słowa x3 i x4
        bit = i % 64

        out = Builder.var(f"{prefix}_S{word}_{bit}")

        Builder.xor([
            out,
            state[word][bit],
            key[i]
        ])

        state[word][bit] = out

    return state


def finalization(Builder, state, key):
    # 1. Klucz XOR-owany ze słowami x1, x2
    state = xor_key_x1_x2(
        Builder,
        state,
        key,
        prefix="final_key_xor_1"
    )

    # 2. Permutacja 12 rund
    state = p12(
        Builder,
        state,
        prefix="final_p12_"
    )

    # 3. Klucz XOR-owany ze słowami x3, x4
    state = xor_key_x3_x4(
        Builder,
        state,
        key,
        prefix="final_key_xor_2"
    )

    return state


def extract_tag(state):
    # Tag to 128 bitów wyciągnięte ze słów x3 oraz x4
    tag = state[3] + state[4]
    return tag