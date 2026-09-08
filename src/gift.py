from .functions import sbox


GIFT_SBOX = [
    0x1, 0xA, 0x4, 0xC,
    0x6, 0xF, 0x3, 0x9,
    0x2, 0xD, 0xB, 0x7,
    0x5, 0x0, 0x8, 0xE
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