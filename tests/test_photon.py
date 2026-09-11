from pysat.solvers import Kissat404
from src.basics import BasicFunctions
from src.photon import add_constant_photon, RC, IC
from src.photon import shift_rows_photon
from src.photon import sbox_photon, Sboxphoton
from src.photon import mix_columns_photon
from src.photon import photon_permutation
from src.photon import create_state
from src.full_photon import init_state, split_state, photon_beetle

def set_cell(builder, cell, value):

    for b in range(4):
        bit = (value >> b) & 1
        if bit == 1:
            builder.cnf.append([cell[b]])
        else:
            builder.cnf.append([-cell[b]])

def test_add_constant_photon():

    builder = BasicFunctions()

    state = []
    new_state = []

    for i in range(8):
        state_row = []
        new_state_row = []

        for j in range(8):
            state_nibble = []
            new_state_nibble = []

            for b in range(4):
                state_nibble.append(
                    builder.var(f"state_{i}_{j}_{b}")
                )
                new_state_nibble.append(
                    builder.var(f"new_{i}_{j}_{b}")
                )

            state_row.append(state_nibble)
            new_state_row.append(new_state_nibble)

        state.append(state_row)
        new_state.append(new_state_row)

  
    add_constant_photon(builder, state, new_state, 0)

    for i in range(8):
        for j in range(8):
            for b in range(4):
                builder.cnf.append([-state[i][j][b]])

    solver = Kissat404()

    for clause in builder.cnf.clauses:
        solver.add_clause(clause)

    assert solver.solve()

    model = solver.get_model()

    for i in range(8):
        constant = RC[0] ^ IC[i]
        for b in range(4):
            expected = (constant >> b) & 1
            variable = new_state[i][0][b]
            if expected == 1:
                assert variable in model
            else:
                assert -variable in model

    for i in range(8):
        for j in range(1, 8):
            for b in range(4):
                assert -new_state[i][j][b] in model


def test_shift_rows_photon():
    builder = BasicFunctions()

    state = []
    new_state = []

    for i in range(8):
            state_row = []
            new_state_row = []
    
            for j in range(8):
                state_nibble = []
                new_state_nibble = []
    
                for b in range(4):
                    state_nibble.append(
                        builder.var(f"state_{i}_{j}_{b}")
                    )
                    new_state_nibble.append(
                        builder.var(f"new_{i}_{j}_{b}")
                    )
    
                state_row.append(state_nibble)
                new_state_row.append(new_state_nibble)
    
            state.append(state_row)
            new_state.append(new_state_row)
    
      
    shift_rows_photon(builder, state, new_state)

    for i in range(8):
        for j in range(8):
            set_cell(builder, state[i][j], j)

    solver = Kissat404()

    for clause in builder.cnf.clauses:
        solver.add_clause(clause)

    assert solver.solve()

    model = solver.get_model()

    for i in range(8):
        for j in range(8):
            expected = (j + i) % 8
            for b in range(4):
                expected_bit = (expected >> b) & 1
                variable = new_state[i][j][b]
                if expected_bit == 1:
                    assert variable in model
                else:
                    assert -variable in model


def test_sbox_photon():
    builder = BasicFunctions()

    state = []
    new_state = []

    for i in range(8):
            state_row = []
            new_state_row = []
    
            for j in range(8):
                state_nibble = []
                new_state_nibble = []
    
                for b in range(4):
                    state_nibble.append(
                        builder.var(f"state_{i}_{j}_{b}")
                    )
                    new_state_nibble.append(
                        builder.var(f"new_{i}_{j}_{b}")
                    )
    
                state_row.append(state_nibble)
                new_state_row.append(new_state_nibble)
    
            state.append(state_row)
            new_state.append(new_state_row)

    sbox_photon(builder, state, new_state)

    for i in range(8):
        for j in range(8):
            set_cell(builder, state[i][j], j) 

    solver = Kissat404()
    
    for clause in builder.cnf.clauses:
            solver.add_clause(clause)
    
    assert solver.solve()
    model = solver.get_model()

    for i in range(8):
        for j in range(8):
            expected = Sboxphoton[j]

            for b in range(4):
                expected_bit = (expected >> b) & 1
                variable = new_state[i][j][b]

                if expected_bit == 1:
                    assert variable in model
                else:
                    assert -variable in model


def test_mix_columns_photon():

    builder = BasicFunctions()

    state = []
    new_state = []

    for i in range(8):
            state_row = []
            new_state_row = []
    
            for j in range(8):
                state_nibble = []
                new_state_nibble = []
    
                for b in range(4):
                    state_nibble.append(
                        builder.var(f"state_{i}_{j}_{b}")
                    )
                    new_state_nibble.append(
                        builder.var(f"new_{i}_{j}_{b}")
                    )
    
                state_row.append(state_nibble)
                new_state_row.append(new_state_nibble)
    
            state.append(state_row)
            new_state.append(new_state_row)


    input_values = [
        [0, 1, 2, 3, 4, 5, 6, 7],
        [8, 9, 10, 11, 12, 13, 14, 15],
        [0, 1, 2, 3, 4, 5, 6, 7],
        [8, 9, 10, 11, 12, 13, 14, 15],
        [0, 1, 2, 3, 4, 5, 6, 7],
        [8, 9, 10, 11, 12, 13, 14, 15],
        [0, 1, 2, 3, 4, 5, 6, 7],
        [8, 9, 10, 11, 12, 13, 14, 15],
    ]

    expected = [
    [8, 14, 4, 2, 3, 5, 15, 9],
    [8, 15, 6, 1, 7, 0, 9, 14],
    [6, 15, 7, 14, 4, 13, 5, 12],
    [6, 5, 0, 3, 10, 9, 12, 15],
    [4, 11, 9, 6, 13, 2, 0, 15],
    [7, 13, 0, 10, 9, 3, 14, 4],
    [13, 6, 8, 3, 7, 12, 2, 9],
    [3, 4, 13, 10, 12, 11, 2, 5],
    ]
    for i in range(8):
        for j in range(8):
            set_cell(builder, state[i][j], input_values[i][j])

    mix_columns_photon(builder, state, new_state, f"test")


    solver = Kissat404()
    
    for clause in builder.cnf.clauses:
            solver.add_clause(clause)
    
    assert solver.solve()
    model = solver.get_model()  

    for i in range(8):
        for j in range(8):

            value = expected[i][j]

            for b in range(4):
                variable = new_state[i][j][b]
                expected_bit = (value>>b)&1
                if expected_bit == 1:
                    assert variable in model
                else:
                    assert -variable in model

    
def test_photon_permutation():
    builder = BasicFunctions()

    state = create_state(builder, "state")

    input_state = [
    [0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7],
    [0x8, 0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF],
    [0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7],
    [0x8, 0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF],
    [0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7],
    [0x8, 0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF],
    [0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7],
    [0x8, 0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF],
]


    expected = [
    [0x9, 0x4, 0xA, 0x0, 0xB, 0xF, 0xD, 0xC],
    [0x7, 0xD, 0xB, 0x9, 0x5, 0x4, 0xB, 0x3],
    [0xF, 0x3, 0xA, 0x8, 0x4, 0x6, 0x7, 0x0],
    [0xE, 0xF, 0x8, 0x8, 0x8, 0x1, 0xD, 0x9],
    [0x1, 0x2, 0x7, 0x0, 0x6, 0xD, 0xC, 0xA],
    [0x3, 0x1, 0x6, 0x9, 0x0, 0xE, 0xD, 0x1],
    [0xB, 0x7, 0x8, 0xD, 0x3, 0xD, 0xC, 0xC],
    [0xA, 0x5, 0x8, 0xB, 0x3, 0x7, 0x4, 0x0],
]

    for i in range(8):
        for j in range(8):
            set_cell(builder, state[i][j], input_state[i][j])

    result = photon_permutation(builder, state, "test")

    solver = Kissat404()
        
    for clause in builder.cnf.clauses:
            solver.add_clause(clause)
        
    assert solver.solve()
    model = solver.get_model()  
    
    for i in range(8):
        for j in range(8):
    
            value = expected[i][j]
    
            for b in range(4):
                variable = result[i][j][b]
                expected_bit = (value>>b)&1
                if expected_bit == 1:
                    assert variable in model
                else:
                    assert -variable in model

def test_init_state():
    nonce = [0]*128
    key = [0]*128
    last_byte = last_byte = [(0xA0 >> b) & 1 for b in range(8)]
    key[-8:] = last_byte
    state = init_state(nonce, key)
    Y, Z = split_state(state)
    bits = Y+Z
    assert bits[248:256] == [0, 0, 0, 0, 0, 1, 0, 1]


#w oficjalnym repo biorą lownibble-highnibble, czyli na odwrot
def hex_to_sat(Builder, input, prefix):
    input_bits = [] 
    for i in range(0, len(input), 2):
        byte = int(input[i:i+2], 16)
        low_nibble = byte & 0xF
        high_nibble = byte >> 4
        low_bits = [(low_nibble >> b) & 1 for b in range(4)]
        high_bits = [(high_nibble >> b) & 1 for b in range(4)]
        input_bits.extend(low_bits)
        input_bits.extend(high_bits)
    sat_bits = []
    for i in range(len(input_bits)):
        v = Builder.var(f"{prefix}_{i}")
        if input_bits[i] == 0:
            Builder.cnf.append([-v])
        else:
            Builder.cnf.append([v])
        sat_bits.append(v)
    return sat_bits

def set_expected_hex(Builder, variables, hex_string):
    expected_bits = []
    for i in range(0, len(hex_string), 2):
        byte = int(hex_string[i: i+2], 16)
        low_nibble = byte & 0xF
        high_nibble = byte >> 4
        low_bits = [(low_nibble >> b) & 1 for b in range(4)]
        high_bits = [(high_nibble >> b) & 1 for b in range(4)]
        expected_bits.extend(low_bits)
        expected_bits.extend(high_bits)
    assert len(variables) == len(expected_bits)
    for i in range(len(variables)):
        if expected_bits[i] == 0:
            Builder.cnf.append([-variables[i]])
        else:
            Builder.cnf.append([variables[i]])

def test_photon_beetle_kat1():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder,"000102030405060708090A0B0C0D0E0F","nonce")
    A = []
    ptx = []
    ciphertext, tag = photon_beetle(builder,nonce,key,A,ptx)
    assert ciphertext == []
    set_expected_hex(builder,tag,"DF4E0BAC1162408098FA5CF084D8F464")
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()

def test_photon_beetle_kat2():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "00", "AD")
    ptx = []
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    assert ciphertext == []
    set_expected_hex(builder, tag, "E840449949081C5378E01EBA6046DBE8")
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()

def test_photon_beetle_kat3():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "0001", "AD")
    ptx = []
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    assert ciphertext == []
    set_expected_hex(builder, tag, "9535FE42756917B946D74128639AA8A7")
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()
    
def test_photon_beetle_kat7():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "000102030405", "AD")
    ptx = []
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    assert ciphertext == []
    set_expected_hex(builder, tag, "DB57E61B4AFB2C2590966CEB67848F57")
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()

def test_photon_beetle_kat22():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F1011121314", "AD")
    ptx = []
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    assert ciphertext == []
    set_expected_hex(builder, tag, "4643F0313C40F4F67DBE416F5768CD32")
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()

def test_photon_beetle_kat27():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F10111213141516171819", "AD")
    ptx = []
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    assert ciphertext == []
    set_expected_hex(builder, tag, "A5E75C1C74A3D29A17A4ADF21F79846F")
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()

def test_photon_beetle_kat50():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "AD")
    ptx = hex_to_sat(builder, "00", "ptx")
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    split = len(ptx) // 4
    expected = "87ACAF9C058BB0EF9FD10C92DFA4D140B5"
    expected_ciphertext = expected[:split]
    expected_tag = expected[split:]
    set_expected_hex(builder, ciphertext, expected_ciphertext)
    set_expected_hex(builder, tag, expected_tag)
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()

def test_photon_beetle_kat265():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    ptx = hex_to_sat(builder, "0001020304050607", "ptx")
    A = []
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    split = len(ptx) // 4
    expected = "A7B9AF5BA1AA580961E102ED01CDB5FD78D1DF643CC7B703"
    expected_ciphertext = expected[:split]
    expected_tag = expected[split:]
    set_expected_hex(builder, ciphertext, expected_ciphertext)
    set_expected_hex(builder, tag, expected_tag)
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()

def test_photon_beetle_kat285():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F10111213", "AD")
    ptx = hex_to_sat(builder, "0001020304050607", "ptx")
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    split = len(ptx) // 4
    expected = "67019C517B020AE1093F5EA03650D6C6919F174CF73A6988"
    expected_ciphertext = expected[:split]
    expected_tag = expected[split:]
    set_expected_hex(builder, ciphertext, expected_ciphertext)
    set_expected_hex(builder, tag, expected_tag)
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()

def test_photon_beetle_kat298():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = []
    ptx = hex_to_sat(builder, "000102030405060708", "ptx")
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    split = len(ptx) // 4
    expected = "A7B9AF5BA1AA5809767F5407C6AA2CEE6C2727CD777CB2BFDC"
    expected_ciphertext = expected[:split]
    expected_tag = expected[split:]
    set_expected_hex(builder, ciphertext, expected_ciphertext)
    set_expected_hex(builder, tag, expected_tag)
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()


def test_photon_beetle_kat430():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = []
    ptx = hex_to_sat(builder, "000102030405060708090A0B0C", "ptx")
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    split = len(ptx) // 4
    expected = "A7B9AF5BA1AA5809768392297480C613958F73817252940CC22C48A4FF"
    expected_ciphertext = expected[:split]
    expected_tag = expected[split:]
    set_expected_hex(builder, ciphertext, expected_ciphertext)
    set_expected_hex(builder, tag, expected_tag)
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()


def test_photon_beetle_kat454():
    builder = BasicFunctions()
    key = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "key")
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F1011121314151617", "AD")
    ptx = hex_to_sat(builder, "000102030405060708090A0B0C", "ptx")
    ciphertext, tag = photon_beetle(builder, nonce, key, A, ptx)
    split = len(ptx) // 4
    expected = "94103789DE1CFE6C7224F1E6EC2A9E64F158B76D40DA75DA5489760A03"
    expected_ciphertext = expected[:split]
    expected_tag = expected[split:]
    set_expected_hex(builder, ciphertext, expected_ciphertext)
    set_expected_hex(builder, tag, expected_tag)
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    assert solver.solve()

