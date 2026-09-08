from .basics import *
from itertools import product

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

def sbox(builder, input_vars, sbox_table, output_size, prefix="sbox"):
    input_size = len(input_vars)

    output_vars = []

    for i in range(output_size):
        output_var = builder.var(f"{prefix}_out_{i}")
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

        for possible_output in product([0, 1], repeat=output_size):

            if list(possible_output) == expected_bits:
                continue

            clause = []

            for var, bit in zip(input_vars, input_bits):
                if bit == 0:
                    clause.append(var)
                else:
                    clause.append(-var)

            for var, bit in zip(output_vars, possible_output):
                if bit == 0:
                    clause.append(var)
                else:
                    clause.append(-var)

            builder.cnf.append(clause)

    return output_vars