from src.ASCON.permutation import p6


def create_plaintext(Builder, size, prefix="plaintext"):
    plaintext = []

    for bit in range(size):
        var = Builder.var(f"{prefix}_{bit}")
        plaintext.append(var)

    return plaintext


def split_into_blocks(bits, block_size=64):
    blocks = []

    for i in range(0, len(bits), block_size):
        block = bits[i:i + block_size]
        blocks.append(block)

    return blocks


def xor_plaintext_block(Builder, state, block, prefix="plaintext"):
    output = []

    for i in range(64):
        out = Builder.var(f"{prefix}_xor_{i}")

        Builder.xor([
            out,
            state[0][i],
            block[i]
        ])

        output.append(out)

    return output


def process_plaintext_block(Builder, state, block, prefix="plaintext"):
    ciphertext_block = xor_plaintext_block(
        Builder,
        state,
        block,
        prefix=f"{prefix}_xor"
    )

    state[0] = ciphertext_block

    state = p6(
        Builder,
        state,
        prefix=f"{prefix}_p6_"
    )

    return state, ciphertext_block


def pad_block(block, block_size=64):
    if len(block) == block_size:
        return block

    padded = block.copy()
    padded.append(1)

    while len(padded) < block_size:
        padded.append(0)

    return padded


def process_plaintext(Builder, state, plaintext):
    if len(plaintext) == 0:
        return state, []

    blocks = split_into_blocks(plaintext, 64)
    ciphertext = []

    for i, block in enumerate(blocks):
        prefix = f"plaintext_block_{i}_"

        # Pełny blok
        if len(block) == 64:
            state, ciphertext_block = process_plaintext_block(
                Builder,
                state,
                block,
                prefix=prefix
            )

            ciphertext.extend(ciphertext_block)

        
        else:
            padded_block = pad_block(block, 64)

            state, ciphertext_block = process_plaintext_block(
                Builder,
                state,
                padded_block,
                prefix=prefix
            )

            
            ciphertext.extend(ciphertext_block[:len(block)])

    return state, ciphertext










from src.ASCON.permutation import p6
from src.ASCON.constants import get_const_zero, get_const_one


def create_plaintext(Builder, size, prefix="plaintext"):
    plaintext = []

    for bit in range(size):
        var = Builder.var(f"{prefix}_{bit}")
        plaintext.append(var)

    return plaintext


def split_into_blocks(bits, block_size=64):
    blocks = []

    for i in range(0, len(bits), block_size):
        block = bits[i:i + block_size]
        blocks.append(block)

    return blocks


def xor_plaintext_block(Builder, state, block, prefix="plaintext"):
    output = []

    for i in range(64):
        out = Builder.var(f"{prefix}_xor_{i}")

        Builder.xor([
            out,
            state[0][i],
            block[i]
        ])

        output.append(out)

    return output


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


def process_plaintext(Builder, state, plaintext):
    # Przygotowanie bloków z gwarantowanym paddingem (100...0)
    padded_plaintext = plaintext.copy()
    padded_plaintext.append(get_const_one(Builder))
    
    while len(padded_plaintext) % 64 != 0:
        padded_plaintext.append(get_const_zero(Builder))

    blocks = split_into_blocks(padded_plaintext, 64)
    ciphertext = []
    total_blocks = len(blocks)

    for i, block in enumerate(blocks):
        prefix = f"plaintext_block_{i}_"

        # 1. Wyliczenie bloku szyfrogramu (XOR z x0)
        ct_block = xor_plaintext_block(
            Builder,
            state,
            block,
            prefix=prefix
        )

        # 2. Podmiana x0 w stanie na wyliczony ct_block
        state[0] = ct_block

        # 3. Dołączanie odpowiedniej liczby bitów szyfrogramu
        if i == total_blocks - 1:
            # Ostatni blok: obcinamy szyfrogram do realnej długości reszty tekstu
            rem = len(plaintext) % 64
            ciphertext.extend(ct_block[:rem])
            # WAŻNE: Po ostatnim bloku NIE wykonuje się p6!
        else:
            # Dla bloków pośrednich: dodajemy pełne 64 bity CT i miksujemy p6
            ciphertext.extend(ct_block)
            state = p6(
                Builder,
                state,
                prefix=f"{prefix}_p6_"
            )

    return state, ciphertext