from pysat.solvers import Kissat404
from basics import BasicFunctions
from photon import add_constant_photon, RC, IC
from photon import shift_rows_photon


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