from functions import *

def add_constant_photon(Builder, state, new_state, k):
    for i in range(8):
        constant = RC[k] ^ IC[i]
        constant_bits = [(constant >> j) & 1 for j in range(4)]
        xor_const(Builder, state[i][0], new_state[i][0], constant_bits)
    for j in range(1, 8):
        for i in range(8):
            for b in range(4):
                Builder.equals(state[i][j][b], new_state[i][j][b])

def shift_rows_photon(Builder, state, new_state):
    for i in range(8):
        for j  in range(8):
            for b in range(4):
                Builder.equals(new_state[i][j][b], state[i][(i + j) % 8][b])

def sbox_photon(Builder, state, new_state):
    for i in range(8):
        for j in range(8):

            for index in range(16):
                output = SBOXphoton[index]

                input_bits = [(index >> b) & 1 for b in range(4)]
                output_bits = [(output >> b) & 1 for b in range(4)]

                
                for b in range(4):

                    clause = []

                    for k in range(4):
                        if input_bits[k] == 0:
                            clause.append(state[i][j][k])
                        else:
                            clause.append(-state[i][j][k])

                    if output_bits[b] == 0:
                        clause.append(-new_state[i][j][b])
                    else:
                        clause.append(new_state[i][j][b])

                    Builder.cnf.append(clause)
            

def mix_columns_photon(Builder, state, new_state):

    for l in range(8):
        column = [state[j][l] for j in range(8)]
        products = gf16_const_mult(Builder, column)

        for i in range(7):
            for bit in range(4):
                Builder.equals(new_state[i][l][bit], column[i+1][bit])


        for bit in range(4):
            Builder.xor([new_state[7][l][bit] + product[bit] for product in products])

    