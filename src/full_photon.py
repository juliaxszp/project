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
def padozs(block, block_size = 128):
    padded_block = block.copy()   #dodaje zeby nie psuc dlugosci ctx
    n = len(padded_block)
    if n < block_size:
        padded_block.append(1)
        for i in range(n+1, block_size):
            padded_block.append(0)
    return padded_block

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
    permuted_state = photon_permutation(Builder, state, "ADfirst")
    Y, Z = split_state(permuted_state)
    blocks = split_blocks(A, 128)
    blocks[-1] = padozs(blocks[-1], 128)
    W = xor_block(Builder, Y, blocks[0], "AD_0")
    new_state = unsplit_state(W + Z)
    return new_state, blocks

def photon256next(Builder, state, blocks, prefix):
    for i in range(1, len(blocks)):
        permuted_state = photon_permutation(Builder, state, f"{prefix}_ {i}") 
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

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#dodajemy do akcji plaintext

def photon256withPTXfirst(Builder, state, ptx):
    permuted_state = photon_permutation(Builder, state, "ptxfirst")
    Y, Z = split_state(permuted_state)
    S = shuffle(Y)
    message_blocks = split_blocks(ptx, 128)
    M1 = message_blocks[0]
    C1 = xor_block(Builder, S, M1, "C_0")
    padded_M1 = padozs(M1, 128) #robie padding dopiero po liczeniu C1, bo ctx ma miec dlugosc ptx
    W = xor_block(Builder, Y, padded_M1, "Wptx_0")
    new_state = unsplit_state(W + Z)
    return new_state, C1, message_blocks

def photon256withPTXnext(Builder, state, message_blocks, C1):
    ciphertext_blocks = []
    ciphertext_blocks.append(C1)
    for i in range(1, len(message_blocks)):
        permuted_state = photon_permutation(Builder, state,f"PTX_{i}")
        Y, Z = split_state(permuted_state)
        S = shuffle(Y)
        Ci = xor_block(Builder, S, message_blocks[i], f"C{i}")
        ciphertext_blocks.append(Ci)
        padded_ms = padozs(message_blocks[i], 128)
        W = xor_block(Builder, Y, padded_ms, f"Wptx_{i}")
        state = unsplit_state(W + Z)
    return state, ciphertext_blocks

def get_c(A, ptx, block_size = 128):
        A_full = len(A) % block_size == 0
        ptx_full = len(ptx) % block_size == 0
        A_exists = len(A)>0
        ptx_exists = len(ptx) > 0

        match(ptx_exists, A_full):
            case(True, True):
                c0 = 1
            case(True, False):
                c0 = 2
            case(False, True):
                c0 = 3
            case(False, False):
                c0 = 4

        match(A_exists, ptx_full):
            case(True, True):
                c1 = 1
            case(True, False):
                c1 = 2
            case(False, True):
                c1 = 5
            case(False, False):
                c1 = 6
        return c0, c1

def domain_constant(Builder, state, c, prefix):
    Y, Z = split_state(state)
    bits = Y+Z
    new_bits = bits.copy()
    c_bits = [(c >> b) & 1 for b in range(3)]
    for b in range(3):
        x = Builder.var(f"{prefix}_domain_{b}")
        if c_bits[b] == 0:
            Builder.equals(x, bits[253+b])
        else:
            Builder.equals_not(x, bits[253 + b])
        new_bits[253+b] = x
    return unsplit_state(new_bits)

def generate_tag(Builder, state):
    permuted_state = photon_permutation(Builder, state, "tag")
    Y, Z = split_state(permuted_state)
    tag = Y
    return tag

def photon_beetle_empty(Builder, nonce, key):
    state = init_state(nonce, key)
    state = domain_constant(Builder, state, 1, "empty")
    tag = generate_tag(Builder, state)
    ciphertext = []
    return ciphertext, tag

def photon_beetle_ad_only(Builder, nonce, key, A):
    c0, c1 = get_c(A, [])
    state, blocks = photon256first(Builder, nonce, key, A)
    state = photon256next(Builder, state, blocks, "ADonly")
    state = domain_constant(Builder, state, c0, "ADonly")
    tag = generate_tag(Builder, state)
    ciphertext = []
    return ciphertext, tag

def photon_beetle(Builder, nonce, key, A, ptx):
    if A == [] and ptx == []:
        ciphertext, tag = photon_beetle_empty(Builder, nonce, key)
        return ciphertext, tag
    elif A != [] and ptx == []:
        ciphertext, tag = photon_beetle_ad_only(Builder, nonce, key, A)
        return ciphertext, tag
    elif A == [] and ptx != []:
        state = init_state(nonce, key)
        c0, c1 = get_c(A, ptx)
        state, C1, message_blocks = photon256withPTXfirst(Builder, state, ptx)
        ciphertext = []
        state, ciphertext_blocks = photon256withPTXnext(Builder, state, message_blocks, C1)
        for block in ciphertext_blocks:
            ciphertext.extend(block)
        
        state = domain_constant(Builder, state, c1, "PTXonly")
        tag = generate_tag(Builder, state)
        return ciphertext, tag
    else:
        state, blocks = photon256first(Builder, nonce, key, A)
        c0, c1 = get_c(A, ptx)
        state = photon256next(Builder, state, blocks, "ADAndPTX")
        state = domain_constant(Builder, state, c0, "AD")
        state, C1, message_blocks= photon256withPTXfirst(Builder, state, ptx)
        ciphertext = []
        state, ciphertext_blocks = photon256withPTXnext(Builder, state, message_blocks, C1)
        for block in ciphertext_blocks:
            ciphertext.extend(block)
        state = domain_constant(Builder, state, c1, "PTX")
        tag = generate_tag(Builder, state)
        return ciphertext, tag

