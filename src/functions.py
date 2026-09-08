from .basics import *
from itertools import product

# Constants for PHOTON
RC = [1, 3, 7, 14, 13, 11, 6, 12, 9, 2, 5, 10]

IC = [0, 1, 3, 7, 15, 14, 12, 8]

Sboxphoton = [
    0xC, 0x5, 0x6, 0xB,
    0x9, 0x0, 0xA, 0xD,
    0x3, 0xE, 0xF, 0x8,
    0x4, 0x7, 0x1, 0x2
]

GF16photon = [
    0x2, 0x4, 0x2, 0xB,
    0x2, 0x8, 0x5, 0x6
]

def permutation(Builder, input_vars, perm):
    output_vars = []

    for i in range(len(perm)):
        input_var = input_vars[perm[i]]
        output_var = Builder.var(f"out_{i}")

        Builder.equals(output_var, input_var)

        output_vars.append(output_var)

    return output_vars

def xor_bits(Builder, x, y, b):
    if b == 0:
        Builder.equals(x, y)
    else:
        Builder.equals_not(x, y)

def xor_const(Builder, var_1, var_2, var_3):
    for i in range(len(var_1)):
        xor_bits(Builder, var_1[i], var_2[i], var_3[i])

def add_round_key(Builder, state_vars, key_vars):
    output_vars = []

    for i in range(len(state_vars)):
        output_var = Builder.var(f"add_round_key_{i}")

        Builder.xor([
            state_vars[i],
            key_vars[i],
            output_var
        ])

        output_vars.append(output_var)

    return output_vars

def sbox(
    builder,
    input_vars,
    sbox_table,
    output_size,
    prefix="sbox"
):
    input_size = len(input_vars)

    output_vars = []

    for i in range(output_size):
        output_var = builder.var(
            f"{prefix}_out_{i}"
        )
        output_vars.append(output_var)

    for input_value in range(2 ** input_size):
        expected_output = sbox_table[input_value]

        input_bits = []

        for i in range(input_size):
            bit = (input_value >> i) & 1
            input_bits.append(bit)

        expected_bits = []

        for i in range(output_size):
            bit = (expected_output >> i) & 1
            expected_bits.append(bit)

        for possible_output in product(
            [0, 1],
            repeat=output_size
        ):
            if list(possible_output) == expected_bits:
                continue

            clause = []

            for var, bit in zip(
                input_vars,
                input_bits
            ):
                if bit == 0:
                    clause.append(var)
                else:
                    clause.append(-var)

            for var, bit in zip(
                output_vars,
                possible_output
            ):
                if bit == 0:
                    clause.append(var)
                else:
                    clause.append(-var)

            builder.cnf.append(clause)

    return output_vars

def gf16_mul(Builder, var_a, var_b, prefix):
    temp = []

    for i in range(4):
        for j in range(4):
            t = Builder.var(
                f"{prefix}_temp_{i}{j}"
            )

            Builder.equal_and(
                t,
                [var_a[i], var_b[j]]
            )

            temp.append(t)

    c0 = Builder.var(f"{prefix}_c0")
    c1 = Builder.var(f"{prefix}_c1")
    c2 = Builder.var(f"{prefix}_c2")
    c3 = Builder.var(f"{prefix}_c3")
    c4 = Builder.var(f"{prefix}_c4")
    c5 = Builder.var(f"{prefix}_c5")
    c6 = Builder.var(f"{prefix}_c6")

    Builder.equals(c0, temp[0])

    Builder.xor([
        c1,
        temp[1],
        temp[4]
    ])

    Builder.xor([
        c2,
        temp[2],
        temp[5],
        temp[8]
    ])

    Builder.xor([
        c3,
        temp[3],
        temp[6],
        temp[9],
        temp[12]
    ])

    Builder.xor([
        c4,
        temp[7],
        temp[10],
        temp[13]
    ])

    Builder.xor([
        c5,
        temp[11],
        temp[14]
    ])

    Builder.equals(
        c6,
        temp[15]
    )

    r0 = Builder.var(f"{prefix}_r0")
    r1 = Builder.var(f"{prefix}_r1")
    r2 = Builder.var(f"{prefix}_r2")
    r3 = Builder.var(f"{prefix}_r3")

    Builder.xor([
        r0,
        c0,
        c4
    ])

    Builder.xor([
        r1,
        c1,
        c4,
        c5
    ])

    Builder.xor([
        r2,
        c2,
        c5,
        c6
    ])

    Builder.xor([
        r3,
        c3,
        c6
    ])

    return [r0, r1, r2, r3]


def gf16_const_mult(
    Builder,
    var_a,
    prefix
):
    result = []

    for i in range(8):
        constant = GF16photon[i]

        constant_bits = [
            (constant >> j) & 1
            for j in range(4)
        ]

        var_b = []

        for j in range(4):
            c = Builder.var(
                f"{prefix}_constant_{i}_{j}"
            )

            if constant_bits[j] == 1:
                Builder.cnf.append([c])
            else:
                Builder.cnf.append([-c])

            var_b.append(c)

        product = gf16_mul(
            Builder,
            var_a[i],
            var_b,
            f"{prefix}_matrix_{i}"
        )

        result.append(product)

    return result