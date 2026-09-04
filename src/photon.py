from functions import *

def add_constant_photon(self, state, new_state, k):
    for i in range(8):
        constant = RC[k] ^ IC[i]
        constant_bits = [(constant >> j) & 1 for j in range(4)]
        self.xor_const(state[i][0], new_state[i][0], constant_bits)
    for j in range(1, 8):
        for i in range(8):
            self.equals(state[i][j], new_state[i][j])

def shift_rows_photon(self, state, new_state):
    for i in range(8):
        for j  in range(8):
            self.equals(state[i][j], new_state[i][(i + j)% 8])

def subcells_photon(self, state, new_state):
    for i in range(8):
        for j in range(8):
            self.equals(new_state[i][j], Sbox[state[i][j]])

