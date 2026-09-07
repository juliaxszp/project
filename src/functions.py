from .basics import *

#const
RC = [1, 3, 7, 14, 13, 11, 6, 12, 9, 2, 5, 10]
IC = [0, 1, 3, 7, 15, 14, 12, 8]
Sboxphoton = [0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2]
GF16photon = [0x2, 0x4, 0x2, 0xB, 0x2, 0x8, 0x5, 0x6]

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

        Builder.xor([state_vars[i], key_vars[i], output_var])

        output_vars.append(output_var)

    return output_vars