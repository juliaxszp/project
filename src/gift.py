from .functions import sbox, xor_const

GIFT_SBOX = [
    0x1, 0xA, 0x4, 0xC,
    0x6, 0xF, 0x3, 0x9,
    0x2, 0xD, 0xB, 0x7,
    0x5, 0x0, 0x8, 0xE
]

GIFT_PERM = [
    [
        0, 4, 8, 12, 16, 20, 24, 28,
        3, 7, 11, 15, 19, 23, 27, 31,
        2, 6, 10, 14, 18, 22, 26, 30,
        1, 5, 9, 13, 17, 21, 25, 29
    ],
    [
        1, 5, 9, 13, 17, 21, 25, 29,
        0, 4, 8, 12, 16, 20, 24, 28,
        3, 7, 11, 15, 19, 23, 27, 31,
        2, 6, 10, 14, 18, 22, 26, 30
    ],
    [
        2, 6, 10, 14, 18, 22, 26, 30,
        1, 5, 9, 13, 17, 21, 25, 29,
        0, 4, 8, 12, 16, 20, 24, 28,
        3, 7, 11, 15, 19, 23, 27, 31
    ],
    [
        3, 7, 11, 15, 19, 23, 27, 31,
        2, 6, 10, 14, 18, 22, 26, 30,
        1, 5, 9, 13, 17, 21, 25, 29,
        0, 4, 8, 12, 16, 20, 24, 28
    ]
]

GIFT_ROUND_CONSTANTS = [
    0x01, 0x03, 0x07, 0x0F,
    0x1F, 0x3E, 0x3D, 0x3B,
    0x37, 0x2F, 0x1E, 0x3C,
    0x39, 0x33, 0x27, 0x0E,

    0x1D, 0x3A, 0x35, 0x2B,
    0x16, 0x2C, 0x18, 0x30,
    0x21, 0x02, 0x05, 0x0B,
    0x17, 0x2E, 0x1C, 0x38,

    0x31, 0x23, 0x06, 0x0D,
    0x1B, 0x36, 0x2D, 0x1A
]

def gift_subcells(builder, state, prefix="gift_subcells"):
    output_state = [
        [],
        [],
        [],
        []
    ]

    for i in range(32):
        input_vars = [
            state[0][i],
            state[1][i],
            state[2][i],
            state[3][i]
        ]

        output_vars = sbox(
            builder,
            input_vars,
            GIFT_SBOX,
            4,
            f"{prefix}_sbox_{i}"
        )

        output_state[0].append(output_vars[0])
        output_state[1].append(output_vars[1])
        output_state[2].append(output_vars[2])
        output_state[3].append(output_vars[3])

    return output_state

def gift_permbits(builder, state, prefix="gift_permbits"):
    output_state = [
        [],
        [],
        [],
        []
    ]

    for row in range(4):
        for i in range(32):
            output_state[row].append(
                builder.var(f"{prefix}_s{row}_{i}")
            )

    for row in range(4):
        for destination in range(32):
            source = GIFT_PERM[row][destination]

            builder.equals(
                output_state[row][destination],
                state[row][source]
            )

    return output_state

def gift_add_round_key(builder, state, u, v, round_constant, prefix="gift_add_round_key"):
    output_state = [
        [],
        [],
        [],
        []
    ]

    for row in range(4):
        for i in range(32):
            output_var = builder.var(
                f"{prefix}_s{row}_{i}"
            )

            output_state[row].append(output_var)

    for i in range(32):
        builder.equals(
            output_state[0][i],
            state[0][i]
        )

        builder.xor([
            state[1][i],
            v[i],
            output_state[1][i]
        ])

        builder.xor([
            state[2][i],
            u[i],
            output_state[2][i]
        ])

    constant = 0x80000000 | round_constant

    constant_bits = []

    for i in range(32):
        bit = (constant >> i) & 1
        constant_bits.append(bit)

    xor_const(
        builder,
        state[3],
        output_state[3],
        constant_bits
    )

    return output_state

def gift_key_schedule(builder, key_state, prefix="gift_key_schedule"):
    u = key_state[3] + key_state[2]
    v = key_state[7] + key_state[6]

    new_key_state = [
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        []
    ]

    rotated_w6 = []
    rotated_w7 = []

    for i in range(16):
        rotated_w6.append(
            key_state[6][(i + 2) % 16]
        )

        rotated_w7.append(
            key_state[7][(i + 12) % 16]
        )

    source_words = [
        rotated_w6,
        rotated_w7,
        key_state[0],
        key_state[1],
        key_state[2],
        key_state[3],
        key_state[4],
        key_state[5]
    ]

    for word in range(8):
        for i in range(16):
            output_var = builder.var(
                f"{prefix}_w{word}_{i}"
            )

            builder.equals(
                output_var,
                source_words[word][i]
            )

            new_key_state[word].append(
                output_var
            )

    return u, v, new_key_state

def gift_round(builder, state, key_state, round_constant, prefix="gift_round"):
    state_after_subcells = gift_subcells(
        builder,
        state,
        f"{prefix}_subcells"
    )

    state_after_permbits = gift_permbits(
        builder,
        state_after_subcells,
        f"{prefix}_permbits"
    )

    u, v, new_key_state = gift_key_schedule(
        builder,
        key_state,
        f"{prefix}_key_schedule"
    )

    output_state = gift_add_round_key(
        builder,
        state_after_permbits,
        u,
        v,
        round_constant,
        f"{prefix}_add_round_key"
    )

    return output_state, new_key_state

def gift128(builder, state, key_state, prefix="gift128"):
    current_state = state
    current_key_state = key_state

    for round_index in range(40):
        current_state, current_key_state = gift_round(
            builder,
            current_state,
            current_key_state,
            GIFT_ROUND_CONSTANTS[round_index],
            f"{prefix}_round_{round_index}"
        )

    return current_state