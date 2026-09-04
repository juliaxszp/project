from functions import *

def add_constant_photon(Builder, state, new_state, k):
    for i in range(8):
        constant = RC[k] ^ IC[i]
        constant_bits = [(constant >> j) & 1 for j in range(4)]
        Builder.xor_const(state[i][0], new_state[i][0], constant_bits)
    for j in range(1, 8):
        for i in range(8):
            Builder.equals(state[i][j], new_state[i][j])

def shift_rows_photon(Builder, state, new_state):
    for i in range(8):
        for j  in range(8):
            Builder.equals(new_state[i][j], state[i][(i + j)% 8])

def sbox_photon(Builder, state, new_state):
    for i in range(8):
        for j in range(8):
            Builder.equals(new_state[i][j], SBOXphoton[state[i][j]])

def mix_columns_photon(Builder, state, new_state):

    for l in range(8):
        column = [state[j][l] for j in range(8)]
        products = gf16_const_mult(Builder, column)

        for i in range(7):
            for bit in range(4):
                Builder.equals(new_state[i][l][bit], column[i+1][bit])


        for bit in range(4):
            Builder.xor([new_state[7][l][bit] + product[bit] for product in products])

    