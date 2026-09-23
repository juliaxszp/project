from src.basics import BasicFunctions
from src.functions import *
from src.rommulus import *


def _make_state(builder, byte_values=None):
    state_vars = []
    for r in range(4):
        row = []
        for c in range(4):
            byte_vars = [builder.idp.id() for _ in range(8)]
            row.append(byte_vars)
        state_vars.append(row)

    if byte_values is not None:
        for r in range(4):
            for c in range(4):
                byte_val = byte_values[r * 4 + c]
                for b in range(8):
                    bit_val = (byte_val >> b) & 1
                    var = state_vars[r][c][b]
                    if bit_val == 1:
                        builder.cnf.append([var])
                    else:
                        builder.cnf.append([-var])
    return state_vars


def _read_state(result_state, model):
    model_set = set(model)
    output_bytes = []
    for r in range(4):
        for c in range(4):
            byte_val = 0
            for b in range(8):
                var = result_state[r][c][b]
                if var in model_set:
                    byte_val |= (1 << b)
            output_bytes.append(byte_val)
    return output_bytes


def test_shift_rows():
    tests = [
        (
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            [0, 1, 2, 3, 7, 4, 5, 6, 10, 11, 8, 9, 13, 14, 15, 12]
        )
    ]

    for input_bytes, expected_bytes in tests:
        builder = BasicFunctions()

        state_vars = []
        for r in range(4):
            row = []
            for c in range(4):
                byte_vars = [builder.idp.id() for _ in range(8)]
                row.append(byte_vars)
            state_vars.append(row)

        result_state = ShiftRows(builder, state_vars)

        for r in range(4):
            for c in range(4):
                byte_val = input_bytes[r * 4 + c]
                for b in range(8):
                    bit_val = (byte_val >> b) & 1
                    var = state_vars[r][c][b]
                    if bit_val == 1:
                        builder.cnf.append([var])
                    else:
                        builder.cnf.append([-var])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            assert solver.solve()
            model = solver.get_model()

        output_bytes = []
        for r in range(4):
            for c in range(4):
                byte_val = 0
                for b in range(8):
                    var = result_state[r][c][b]
                    if var in model:
                        byte_val |= (1 << b)
                output_bytes.append(byte_val)

        assert output_bytes == expected_bytes


def test_mix_columns():
    tests = [
        (
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            [4, 5, 6, 7, 0, 1, 2, 3, 12, 12, 12, 12, 8, 8, 8, 8]
        )
    ]

    for input_bytes, expected_bytes in tests:
        builder = BasicFunctions()

        state_vars = []
        for r in range(4):
            row = []
            for c in range(4):
                byte_vars = [builder.idp.id() for _ in range(8)]
                row.append(byte_vars)
            state_vars.append(row)

        result_state = MixColumns(builder, state_vars)

        for r in range(4):
            for c in range(4):
                byte_val = input_bytes[r * 4 + c]
                for b in range(8):
                    bit_val = (byte_val >> b) & 1
                    var = state_vars[r][c][b]
                    if bit_val == 1:
                        builder.cnf.append([var])
                    else:
                        builder.cnf.append([-var])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            assert solver.solve()
            model = solver.get_model()

        output_bytes = []
        for r in range(4):
            for c in range(4):
                byte_val = 0
                for b in range(8):
                    var = result_state[r][c][b]
                    if var in model:
                        byte_val |= (1 << b)
                output_bytes.append(byte_val)

        assert output_bytes == expected_bytes


def test_sub_cells():
    input_bytes = list(range(16))
    expected_bytes = [S8[v] for v in input_bytes]

    builder = BasicFunctions()
    state_vars = _make_state(builder, input_bytes)
    result_state = SubCells(builder, state_vars)

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        assert solver.solve()
        model = solver.get_model()

    output_bytes = _read_state(result_state, model)
    assert output_bytes == expected_bytes


def test_sub_cells_full_sbox():
    input_bytes = [0x00, 0x0F, 0x10, 0x1F, 0x2A, 0x3C, 0x55, 0x7F,
                   0x80, 0x99, 0xA5, 0xB3, 0xC7, 0xD8, 0xEE, 0xFF]
    expected_bytes = [S8[v] for v in input_bytes]

    builder = BasicFunctions()
    state_vars = _make_state(builder, input_bytes)
    result_state = SubCells(builder, state_vars)

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        assert solver.solve()
        model = solver.get_model()

    output_bytes = _read_state(result_state, model)
    assert output_bytes == expected_bytes


def test_add_constants_round0():
    input_bytes = [0] * 16
    builder = BasicFunctions()
    state_vars = _make_state(builder, input_bytes)
    result_state = AddConstants(builder, state_vars, round_num=0)

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        assert solver.solve()
        model = solver.get_model()

    output_bytes = _read_state(result_state, model)

    expected_bytes = [0] * 16
    expected_bytes[0] = 0x01
    expected_bytes[4] = 0x00
    expected_bytes[8] = 0x02

    assert output_bytes == expected_bytes


def test_add_constants_round1_nonzero_state():
    input_bytes = list(range(16))  # 0..15
    builder = BasicFunctions()
    state_vars = _make_state(builder, input_bytes)
    result_state = AddConstants(builder, state_vars, round_num=1)

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        assert solver.solve()
        model = solver.get_model()

    output_bytes = _read_state(result_state, model)

    rc = 0x03
    c0 = rc & 0x0F
    c1 = (rc >> 4) & 0x03
    c2 = 0x02

    expected_bytes = list(input_bytes)
    expected_bytes[0] ^= c0
    expected_bytes[4] ^= c1
    expected_bytes[8] ^= c2

    assert output_bytes == expected_bytes


def test_add_round_tweakey():
    state_bytes = list(range(16))
    tk1_bytes = list(range(16))
    tk2_bytes = [((v * 7) + 3) % 256 for v in range(16)]
    tk3_bytes = [((v * 13) + 5) % 256 for v in range(16)]

    builder = BasicFunctions()
    state_vars = _make_state(builder, state_bytes)
    tk1_vars = _make_state(builder, tk1_bytes)
    tk2_vars = _make_state(builder, tk2_bytes)
    tk3_vars = _make_state(builder, tk3_bytes)

    result_state, new_tk1_vars, new_tk2_vars, new_tk3_vars = AddRoundTweakey(
        builder, state_vars, tk1_vars, tk2_vars, tk3_vars
    )

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        assert solver.solve()
        model = solver.get_model()

    output_bytes = _read_state(result_state, model)
    out_tk1 = _read_state(new_tk1_vars, model)
    out_tk2 = _read_state(new_tk2_vars, model)
    out_tk3 = _read_state(new_tk3_vars, model)

    expected_bytes = list(state_bytes)
    for i in range(8):
        expected_bytes[i] ^= tk1_bytes[i] ^ tk2_bytes[i] ^ tk3_bytes[i]
    assert output_bytes == expected_bytes

    PT = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]

    def permute(flat):
        return [flat[PT[i]] for i in range(16)]

    def lfsr_tk2(b):
        x = [(b >> i) & 1 for i in range(8)]
        nx = [x[7] ^ x[5], x[0], x[1], x[2], x[3], x[4], x[5], x[6]]
        return sum(nx[i] << i for i in range(8))

    def lfsr_tk3(b):
        x = [(b >> i) & 1 for i in range(8)]
        nx = [x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[0] ^ x[6]]
        return sum(nx[i] << i for i in range(8))

    exp_tk1 = permute(tk1_bytes)
    exp_tk2 = permute(tk2_bytes)
    exp_tk3 = permute(tk3_bytes)
    for i in range(8):
        exp_tk2[i] = lfsr_tk2(exp_tk2[i])
        exp_tk3[i] = lfsr_tk3(exp_tk3[i])

    assert out_tk1 == exp_tk1
    assert out_tk2 == exp_tk2
    assert out_tk3 == exp_tk3