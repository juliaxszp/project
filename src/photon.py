from functions import *

def addconstantphoton(self, state, new_state, k):
    for i in range(8):
        constant = RC[k] ^ IC[i]
        constant_bits = [(constant >> j) & 1 for j in range(4)]
        self.xor_const(state[i][0], new_state[i][0], constant_bits)
    for j in range(1, 8):
        for i in range(8):
            self.equals(state[i][j], new_state[i][j])


