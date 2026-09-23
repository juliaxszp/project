from src.ASCON.permutation import p6
from src.ASCON.constants import get_const_one


def create_associated_data(Builder, size, prefix="ad"):
    ad = []

    for bit in range(size):
        var = Builder.var(f"{prefix}_{bit}")
        ad.append(var)

    return ad


def split_into_blocks(bits, block_size=64):
    blocks = []

    for i in range(0, len(bits), block_size):
        block = bits[i:i + block_size]
        blocks.append(block)

    return blocks


def xor_ad_block(Builder, state, block, prefix="ad"):
    for i in range(64):
        out = Builder.var(f"{prefix}_xor_{i}")

        Builder.xor([
            out,
            state[0][i],
            block[i]
        ])

        state[0][i] = out

    return state


def process_ad_block(Builder, state, block, prefix="ad"):
    state = xor_ad_block(
        Builder,
        state,
        block,
        prefix=f"{prefix}_xor"
    )

    state = p6(
        Builder,
        state,
        prefix=f"{prefix}_p6_"
    )

    return state


def pad_block(block, block_size=64):
    if len(block) == block_size:
        return block

    padded = block.copy()
    padded.append(1)

    while len(padded) < block_size:
        padded.append(0)

    return padded


def process_associated_data(Builder, state, ad):
    if len(ad) == 0:
        return state

    blocks = split_into_blocks(ad, 64)

    for i, block in enumerate(blocks):
        prefix = f"ad_block_{i}_"

        if len(block) == 64:
            state = process_ad_block(
                Builder,
                state,
                block,
                prefix=prefix
            )

        else:
            block = pad_block(block, 64)

            state = process_ad_block(
                Builder,
                state,
                block,
                prefix=prefix
            )

    # Jeżeli AD jest wielokrotnością 64 bitów,
    # potrzebujemy dodatkowego bloku: 1 || 0...
    if len(ad) % 64 == 0:
        padding_block = pad_block([], 64)

        state = process_ad_block(
            Builder,
            state,
            padding_block,
            prefix=f"ad_block_{len(blocks)}_"
        )

    return state


def domain_separation(Builder, state):
    out = Builder.var("domain_separation")

    Builder.xor([
        out,
        state[4][0],
        1
    ])

    state[4][0] = out

    return state


def associated_data_phase(Builder, state, ad):
    state = process_associated_data(
        Builder,
        state,
        ad
    )

    state = domain_separation(
        Builder,
        state
    )

    return state









from src.ASCON.permutation import p6
from src.ASCON.constants import get_const_one, get_const_zero


def create_associated_data(Builder, size, prefix="ad"):
    ad = []

    for bit in range(size):
        var = Builder.var(f"{prefix}_{bit}")
        ad.append(var)

    return ad


def split_into_blocks(bits, block_size=64):
    blocks = []

    for i in range(0, len(bits), block_size):
        block = bits[i:i + block_size]
        blocks.append(block)

    return blocks


def xor_ad_block(Builder, state, block, prefix="ad"):
    for i in range(64):
        out = Builder.var(f"{prefix}_xor_{i}")

        Builder.xor([
            out,
            state[0][i],
            block[i]
        ])

        state[0][i] = out

    return state


def process_ad_block(Builder, state, block, prefix="ad"):
    state = xor_ad_block(
        Builder,
        state,
        block,
        prefix=f"{prefix}_xor"
    )

    state = p6(
        Builder,
        state,
        prefix=f"{prefix}_p6_"
    )

    return state


from src.ASCON.constants import get_const_zero, get_const_one


def pad_block(block, block_size=64, Builder=None):
    padded = block.copy()

    if Builder is not None:
        padded.append(get_const_one(Builder))
    else:
        padded.append(1)

    while len(padded) % block_size != 0:
        if Builder is not None:
            padded.append(get_const_zero(Builder))
        else:
            padded.append(0)

    return padded


def process_associated_data(Builder, state, ad):
    # Gdy AD jest puste, nie przetwarzamy żadnych bloków danych i nie wywołujemy p6
    if len(ad) == 0:
        return state

    # Przygotowanie bitów AD z pełnym paddingiem (100...0)
    padded_ad = ad.copy()
    padded_ad.append(1)

    while len(padded_ad) % 64 != 0:
        padded_ad.append(0)

    blocks = split_into_blocks(padded_ad, 64)

    # Przetwarzanie wszystkich bloków AD z wywołaniem p6
    for i, block in enumerate(blocks):
        prefix = f"ad_block_{i}_"
        state = process_ad_block(
            Builder,
            state,
            block,
            prefix=prefix
        )

    return state


def domain_separation(Builder, state):
    out = Builder.var("domain_separation")

    # Domain separation wykonuje XOR z 1 na OSTATNIM bicie słowa x4 (indeks 63)
    Builder.xor([
        out,
        state[4][63],
        get_const_one(Builder)
    ])

    state[4][63] = out

    return state


def associated_data_phase(Builder, state, ad):
    # 1. Przetwarzanie danych AD (jeśli występują)
    state = process_associated_data(
        Builder,
        state,
        ad
    )

    # 2. Domain separation wykonuje się ZAWSZE po fazie AD
    state = domain_separation(
        Builder,
        state
    )

    return state