from .basics import *
from .functions import *

S8 = [
    0x65, 0x4c, 0x6a, 0x42, 0x4b, 0x63, 0x43, 0x6b, 0x55, 0x75, 0x5a, 0x7a, 0x53, 0x73, 0x5b, 0x7b,
    0x35, 0x8c, 0x3a, 0x81, 0x89, 0x33, 0x80, 0x3b, 0x95, 0x25, 0x98, 0x2a, 0x90, 0x23, 0x99, 0x2b,
    0xe5, 0xcc, 0xe8, 0xc1, 0xc9, 0xe0, 0xc0, 0xe9, 0xd5, 0xf5, 0xd8, 0xf8, 0xd0, 0xf0, 0xd9, 0xf9,
    0xa5, 0x1c, 0xa8, 0x12, 0x1b, 0xa0, 0x13, 0xa9, 0x05, 0xb5, 0x0a, 0xb8, 0x03, 0xb0, 0x0b, 0xb9,
    0x32, 0x88, 0x3c, 0x85, 0x8d, 0x34, 0x84, 0x3d, 0x91, 0x22, 0x9c, 0x2c, 0x94, 0x24, 0x9d, 0x2d,
    0x62, 0x4a, 0x6c, 0x45, 0x4d, 0x64, 0x44, 0x6d, 0x52, 0x72, 0x5c, 0x7c, 0x54, 0x74, 0x5d, 0x7d,
    0xa1, 0x1a, 0xac, 0x15, 0x1d, 0xa4, 0x14, 0xad, 0x02, 0xb1, 0x0c, 0xbc, 0x04, 0xb4, 0x0d, 0xbd,
    0xe1, 0xc8, 0xec, 0xc5, 0xcd, 0xe4, 0xc4, 0xed, 0xd1, 0xf1, 0xdc, 0xfc, 0xd4, 0xf4, 0xdd, 0xfd,
    0x36, 0x8e, 0x38, 0x82, 0x8b, 0x30, 0x83, 0x39, 0x96, 0x26, 0x9a, 0x28, 0x93, 0x20, 0x9b, 0x29,
    0x66, 0x4e, 0x68, 0x41, 0x49, 0x60, 0x40, 0x69, 0x56, 0x76, 0x58, 0x78, 0x50, 0x70, 0x59, 0x79,
    0xa6, 0x1e, 0xaa, 0x11, 0x19, 0xa3, 0x10, 0xab, 0x06, 0xb6, 0x08, 0xba, 0x00, 0xb3, 0x09, 0xbb,
    0xe6, 0xce, 0xea, 0xc2, 0xcb, 0xe3, 0xc3, 0xeb, 0xd6, 0xf6, 0xda, 0xfa, 0xd3, 0xf3, 0xdb, 0xfb,
    0x31, 0x8a, 0x3e, 0x86, 0x8f, 0x37, 0x87, 0x3f, 0x92, 0x21, 0x9e, 0x2e, 0x97, 0x27, 0x9f, 0x2f,
    0x61, 0x48, 0x6e, 0x46, 0x4f, 0x67, 0x47, 0x6f, 0x51, 0x71, 0x5e, 0x7e, 0x57, 0x77, 0x5f, 0x7f,
    0xa2, 0x18, 0xae, 0x16, 0x1f, 0xa7, 0x17, 0xaf, 0x01, 0xb2, 0x0e, 0xbe, 0x07, 0xb7, 0x0f, 0xbf,
    0xe2, 0xca, 0xee, 0xc6, 0xcf, 0xe7, 0xc7, 0xef, 0xd2, 0xf2, 0xde, 0xfe, 0xd7, 0xf7, 0xdf, 0xff
]

RC = [
    0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3E, 0x3D, 0x3B, 0x37, 0x2F, 0x1E, 0x3C, 0x39, 0x33, 0x27, 0x0E,
    0x1D, 0x3A, 0x35, 0x2B, 0x16, 0x2C, 0x18, 0x30, 0x21, 0x02, 0x05, 0x0B, 0x17, 0x2E, 0x1C, 0x38,
    0x31, 0x23, 0x06, 0x0D, 0x1B, 0x36, 0x2D, 0x1A
]


def SubCells(builder, state_vars):
    new_state = [[None] * 4 for _ in range(4)]

    for r in range(4):
        for c in range(4):
            cur = list(state_vars[r][c])

            for it in range(4):
                x0, x1, x2, x3, x4, x5, x6, x7 = cur

                or1 = builder.idp.id()
                builder.equal_or(or1, [x7, x6])
                nor1 = builder.idp.id()
                builder.equals_not(or1, nor1)
                new_x4 = builder.idp.id()
                builder.xor([new_x4, x4, nor1])

                or2 = builder.idp.id()
                builder.equal_or(or2, [x3, x2])
                nor2 = builder.idp.id()
                builder.equals_not(or2, nor2)
                new_x0 = builder.idp.id()
                builder.xor([new_x0, x0, nor2])

                s0, s1, s2, s3, s4, s5, s6, s7 = new_x0, x1, x2, x3, new_x4, x5, x6, x7

                if it < 3:
                    cur = [s5, s3, s0, s4, s6, s7, s1, s2]
                else:
                    cur = [s0, s2, s1, s3, s4, s5, s6, s7]

            new_state[r][c] = cur

    return new_state


def AddConstants(builder, state_vars, round_num):
    rc = RC[round_num % len(RC)]
    c0 = rc & 0x0F
    c1 = (rc >> 4) & 0x03
    c2 = 0x02

    new_state = [[state_vars[r][c] for c in range(4)] for r in range(4)]

    for (r, c, const_value) in [(0, 0, c0), (1, 0, c1), (2, 0, c2)]:
        byte_vars = state_vars[r][c]
        out = [builder.idp.id() for _ in range(8)]
        for b in range(8):
            bit = (const_value >> b) & 1
            xor_bits(builder, byte_vars[b], out[b], bit)
        new_state[r][c] = out

    return new_state


def AddRoundTweakey(builder, state_vars, tk1_vars, tk2_vars, tk3_vars):
    new_state = [[state_vars[r][c] for c in range(4)] for r in range(4)]
    for r in range(2):
        for c in range(4):
            out = [builder.idp.id() for _ in range(8)]
            for b in range(8):
                builder.xor([
                    out[b],
                    state_vars[r][c][b],
                    tk1_vars[r][c][b],
                    tk2_vars[r][c][b],
                    tk3_vars[r][c][b],
                ])
            new_state[r][c] = out

    PT = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]

    flat_tk1 = [tk1_vars[i // 4][i % 4] for i in range(16)]
    flat_tk2 = [tk2_vars[i // 4][i % 4] for i in range(16)]
    flat_tk3 = [tk3_vars[i // 4][i % 4] for i in range(16)]

    new_tk1 = [[None] * 4 for _ in range(4)]
    new_tk2 = [[None] * 4 for _ in range(4)]
    new_tk3 = [[None] * 4 for _ in range(4)]

    for i in range(16):
        r, c = divmod(i, 4)
        for flat_src, new_tk in ((flat_tk1, new_tk1), (flat_tk2, new_tk2), (flat_tk3, new_tk3)):
            src = flat_src[PT[i]]
            out = [builder.idp.id() for _ in range(8)]
            for b in range(8):
                builder.equals(out[b], src[b])
            new_tk[r][c] = out

    for r in range(2):
        for c in range(4):
            x0, x1, x2, x3, x4, x5, x6, x7 = new_tk2[r][c]
            new_x0 = builder.idp.id()
            builder.xor([new_x0, x7, x5])
            new_tk2[r][c] = [new_x0, x0, x1, x2, x3, x4, x5, x6]

            y0, y1, y2, y3, y4, y5, y6, y7 = new_tk3[r][c]
            new_y7 = builder.idp.id()
            builder.xor([new_y7, y0, y6])
            new_tk3[r][c] = [y1, y2, y3, y4, y5, y6, y7, new_y7]

    return new_state, new_tk1, new_tk2, new_tk3


def ShiftRows(builder, state_vars):
    shift_patterns = [
        [0, 1, 2, 3],
        [3, 0, 1, 2],
        [2, 3, 0, 1],
        [1, 2, 3, 0]
    ]

    new_state = []
    for r in range(4):
        new_row = []
        for c in shift_patterns[r]:
            input_byte = state_vars[r][c]
            output_byte = [builder.idp.id() for _ in range(8)]

            for b in range(8):
                builder.equals(output_byte[b], input_byte[b])

            new_row.append(output_byte)
        new_state.append(new_row)

    return new_state


def MixColumns(builder, state_vars):

    MIX_M = [
        [1, 0, 1, 1],
        [1, 0, 0, 0],
        [0, 1, 1, 0],
        [1, 0, 1, 0]
    ]

    new_state = [[None] * 4 for _ in range(4)]

    for i in range(4):
        a = state_vars[0][i]
        b = state_vars[1][i]
        c = state_vars[2][i]
        d = state_vars[3][i]
        terms = [a, b, c, d]

        for row in range(4):
            selected = [terms[k] for k in range(4) if MIX_M[row][k] == 1]
            output_byte = [builder.idp.id() for _ in range(8)]

            for bit in range(8):
                bits_to_xor = [sel[bit] for sel in selected]
                if len(bits_to_xor) == 1:
                    builder.equals(output_byte[bit], bits_to_xor[0])
                else:
                    builder.xor([output_byte[bit]] + bits_to_xor)

            new_state[row][i] = output_byte

    return new_state