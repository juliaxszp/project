from pysat.solvers import Kissat404
from basics import BasicFunctions
from photon import add_constant_photon, RC, IC
from photon import shift_rows_photon
from photon import sbox_photon, Sboxphoton
from photon import mix_columns_photon
from photon import photon_permutation
from photon import create_state


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

    result = photon_permutation(builder, state)

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