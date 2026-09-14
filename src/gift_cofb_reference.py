from .gift import GIFT_SBOX, GIFT_PERM, GIFT_ROUND_CONSTANTS

def rotate_right_16(value, shift):
    value &= 0xFFFF

    return (
        (value >> shift)
        |
        (value << (16 - shift))
    ) & 0xFFFF

def gift_subcells_reference(state):
    output = [
        0,
        0,
        0,
        0
    ]

    for i in range(32):
        input_value = 0

        for row in range(4):
            bit = (
                state[row] >> i
            ) & 1

            input_value |= (
                bit << row
            )

        sbox_output = (
            GIFT_SBOX[input_value]
        )

        for row in range(4):
            bit = (
                sbox_output >> row
            ) & 1

            if bit == 1:
                output[row] |= (
                    1 << i
                )

    return output

def gift_permbits_reference(state):
    output = [
        0,
        0,
        0,
        0
    ]

    for row in range(4):
        for destination in range(32):
            source = (
                GIFT_PERM[row][destination]
            )

            bit = (
                state[row] >> source
            ) & 1

            if bit == 1:
                output[row] |= (
                    1 << destination
                )

    return output

def gift_add_round_key_reference(state, key_state, round_constant):
    u = (
        (key_state[2] << 16)
        |
        key_state[3]
    )

    v = (
        (key_state[6] << 16)
        |
        key_state[7]
    )

    output = list(state)

    output[1] ^= v
    output[2] ^= u

    output[3] ^= (
        0x80000000
        |
        round_constant
    )

    return output

def gift_key_schedule_reference(key_state):
    return [
        rotate_right_16(
            key_state[6],
            2
        ),

        rotate_right_16(
            key_state[7],
            12
        ),

        key_state[0],
        key_state[1],
        key_state[2],
        key_state[3],
        key_state[4],
        key_state[5]
    ]

def gift128_reference(block, key):
    if len(block) != 16:
        raise ValueError(
            "GIFT block must contain 16 bytes"
        )

    if len(key) != 16:
        raise ValueError(
            "GIFT key must contain 16 bytes"
        )

    state = []

    for row in range(4):
        start = row * 4

        value = int.from_bytes(
            block[start:start + 4],
            byteorder="big"
        )

        state.append(value)

    key_state = []

    for word in range(8):
        start = word * 2

        value = int.from_bytes(
            key[start:start + 2],
            byteorder="big"
        )

        key_state.append(value)

    for round_index in range(40):
        state = (
            gift_subcells_reference(
                state
            )
        )

        state = (
            gift_permbits_reference(
                state
            )
        )

        state = (
            gift_add_round_key_reference(
                state,
                key_state,
                GIFT_ROUND_CONSTANTS[
                    round_index
                ]
            )
        )

        key_state = (
            gift_key_schedule_reference(
                key_state
            )
        )

    output = b""

    for row in state:
        output += row.to_bytes(
            4,
            byteorder="big"
        )

    return output

def cofb_pad_reference(data):
    if (
        len(data) != 0
        and
        len(data) % 16 == 0
    ):
        return data

    padded = (
        data
        +
        b"\x80"
    )

    while len(padded) % 16 != 0:
        padded += b"\x00"

    return padded

def cofb_g_reference(y):
    if len(y) != 16:
        raise ValueError(
            "COFB G expects 16 bytes"
        )

    y1 = int.from_bytes(
        y[:8],
        byteorder="big"
    )

    y2 = y[8:]

    rotated_y1 = (
        (
            (y1 << 1)
            |
            (y1 >> 63)
        )
        &
        0xFFFFFFFFFFFFFFFF
    )

    return (
        y2
        +
        rotated_y1.to_bytes(
            8,
            byteorder="big"
        )
    )

def cofb_double_reference(l):
    carry = (
        l >> 63
    ) & 1

    result = (
        l << 1
    ) & 0xFFFFFFFFFFFFFFFF

    if carry == 1:
        result ^= 0x1B

    return result

def cofb_triple_reference(l):
    return (
        l
        ^
        cofb_double_reference(l)
    )

def cofb_triple_squared_reference(l):
    return cofb_triple_reference(
        cofb_triple_reference(l)
    )

def xor_bytes(*blocks):
    if len(blocks) == 0:
        return b""

    length = len(blocks[0])

    for block in blocks:
        if len(block) != length:
            raise ValueError(
                "All blocks must have "
                "the same length"
            )

    output = bytearray(length)

    for i in range(length):
        value = 0

        for block in blocks:
            value ^= block[i]

        output[i] = value

    return bytes(output)

def cofb_mask_reference(l):
    return (
        l.to_bytes(
            8,
            byteorder="big"
        )
        +
        b"\x00" * 8
    )

def cofb_process_ad_reference(associated_data, y, l, key, message_is_empty):
    padded = cofb_pad_reference(
        associated_data
    )

    blocks = [
        padded[i:i + 16]
        for i in range(
            0,
            len(padded),
            16
        )
    ]

    for block in blocks[:-1]:
        l = cofb_double_reference(l)

        x = xor_bytes(
            block,
            cofb_g_reference(y),
            cofb_mask_reference(l)
        )

        y = gift128_reference(
            x,
            key
        )

    if (
        len(associated_data) != 0
        and
        len(associated_data) % 16 == 0
    ):
        l = cofb_triple_reference(l)

    else:
        l = (
            cofb_triple_squared_reference(
                l
            )
        )

    if message_is_empty:
        l = (
            cofb_triple_squared_reference(
                l
            )
        )

    x = xor_bytes(
        blocks[-1],
        cofb_g_reference(y),
        cofb_mask_reference(l)
    )

    y = gift128_reference(
        x,
        key
    )

    return y, l

def cofb_process_message_reference(message, y, l, key):
    if len(message) == 0:
        return b"", y, l

    message_length = len(message)

    padded = cofb_pad_reference(
        message
    )

    blocks = [
        padded[i:i + 16]
        for i in range(
            0,
            len(padded),
            16
        )
    ]

    ciphertext_blocks = []

    for block in blocks[:-1]:
        l = cofb_double_reference(l)

        ciphertext_block = xor_bytes(
            block,
            y
        )

        ciphertext_blocks.append(
            ciphertext_block
        )

        x = xor_bytes(
            block,
            cofb_g_reference(y),
            cofb_mask_reference(l)
        )

        y = gift128_reference(
            x,
            key
        )

    last_block = blocks[-1]

    if message_length % 16 == 0:
        l = cofb_triple_reference(l)

    else:
        l = (
            cofb_triple_squared_reference(
                l
            )
        )

    ciphertext_block = xor_bytes(
        last_block,
        y
    )

    ciphertext_blocks.append(
        ciphertext_block
    )

    x = xor_bytes(
        last_block,
        cofb_g_reference(y),
        cofb_mask_reference(l)
    )

    y = gift128_reference(
        x,
        key
    )

    ciphertext = b"".join(
        ciphertext_blocks
    )

    ciphertext = ciphertext[
        :message_length
    ]

    return ciphertext, y, l

def gift_cofb_encrypt_reference(key, nonce, associated_data, message):
    if len(key) != 16:
        raise ValueError(
            "Key must contain 16 bytes"
        )

    if len(nonce) != 16:
        raise ValueError(
            "Nonce must contain 16 bytes"
        )

    y = gift128_reference(
        nonce,
        key
    )

    l = int.from_bytes(
        y[:8],
        byteorder="big"
    )

    y, l = cofb_process_ad_reference(
        associated_data,
        y,
        l,
        key,
        message_is_empty=(
            len(message) == 0
        )
    )

    ciphertext, y, l = (
        cofb_process_message_reference(
            message,
            y,
            l,
            key
        )
    )

    tag = y

    return ciphertext, tag