from .photon import *
#Mamy nonce i klucz, ktore sa konkatenowane w IV. Oba maja po 128 bitow

def init_state(nonce, key):
    bits = nonce + key
    state = []
    index = 0
    for i in range(8):
        row = []
        for j in range(8):
            nibble = []
            for b in range(4):
                nibble.append(bits[index])
                index+=1
            row.append(nibble)
        state.append(row)
    return state

#musze podzielic bloki AD na 128 bitow
def split_blocks(AD, block_size = 128):
    blocks = []
    for i in range(0, len(AD), block_size):
        block = AD[i:i+block_size]
        blocks.append(block)
    return blocks

#teraz padding 10*
def padozs(blocks, block_size = 128):
    block = blocks[-1]
    n = len(block)
    if n < block_size:
        block.append(1)
        for i in range(n+1, block_size):
            block.append(0)
    return blocks

#funkcja do podzialu stanow 

def split_state(state):
    bits=[]
    for i in range(8):
        for j in range(8):
            for b in range(4):
                bits.append(state[i][j][b])
    Y = bits[:128]
    Z = bits[128:]

    return Y, Z

#pierwsza funkcja w CNF, bo po permutacji są zmienne SAT POTEM JEST UZYWANA POZA AD TO TEZ DO PLAINTEXTU
def xor_block(Builder, Y, block, prefix):
    result = []

    for i in range(len(block)):
        x = Builder.var(f"{prefix}_{i}")
        Builder.xor([x, Y[i], block[i]])
        result.append(x)

    return result

#funckja permutacji przyjmuje state[i][j][b] a nie plaskie bity, stad musze zrobic odwrotnosc funkcji splits_state
def unsplit_state(bits):
    state = []
    index = 0
    for i in range(8):
        row = []
        for j in range(8):
            nibble = []
            for b in range(4):
                nibble.append(bits[index])
                index+=1
            row.append(nibble)
        state.append(row)
    return state

#------------------------------------
#cosie dzieje w szyfrze przed plaintextem
def photon256first(Builder, nonce, key, A):
    state = init_state(nonce, key)
    permuted_state = photon_permutation(Builder, state)
    Y, Z = split_state(permuted_state)
    blocks = split_blocks(A, 128)
    blocks = padozs(blocks, 128)
    W = xor_block(Builder, Y, blocks[0], "AD_0")
    new_state = unsplit_state(W + Z)
    return new_state, blocks

def photon256next(Builder, state, blocks, prefix):
    for i in range(1, len(blocks)):
        permuted_state = photon_permutation(Builder, state)
        Y, Z = split_state(permuted_state)
        W = xor_block(Builder, Y, blocks[i], f"{prefix}_{i}")
        state = unsplit_state(W + Z)
    return state

#-----------------------------------------------

def shuffle(S):
    half = len(S) // 2
    S1 = S[:half]
    S2 = S[half:]

    rotated_S1 = [S1[-1]] + S1[:-1]
    shuffled = S2 + rotated_S1

    return shuffled
