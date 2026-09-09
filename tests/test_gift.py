from src.basics import BasicFunctions
from src.gift import *
from pysat.solvers import Kissat404

def test_gift_subcells():
    builder = BasicFunctions()

    state = [
        [],
        [],
        [],
        []
    ]

    for row in range(4):
        for i in range(32):
            state[row].append(
                builder.var(f"state_{row}_{i}")
            )

    output_state = gift_subcells(
        builder,
        state,
        "test_subcells"
    )

    input_values = []

    for i in range(32):
        input_values.append(i % 16)

    for column in range(32):
        input_value = input_values[column]

        input_bits = []

        for i in range(4):
            bit = (input_value >> i) & 1
            input_bits.append(bit)

        for row in range(4):
            var = state[row][column]
            bit = input_bits[row]

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()

        model = solver.get_model()

    for column in range(32):
        output_bits = []

        for row in range(4):
            var = output_state[row][column]

            if var in model:
                output_bits.append(1)
            else:
                output_bits.append(0)

        output_value = 0

        for i, bit in enumerate(output_bits):
            output_value |= bit << i

        input_value = input_values[column]
        expected_output = GIFT_SBOX[input_value]

        assert output_value == expected_output

def test_gift_permbits():
    for source in range(32):
        builder = BasicFunctions()

        state = [
            [],
            [],
            [],
            []
        ]

        for row in range(4):
            for i in range(32):
                state[row].append(
                    builder.var(f"state_{row}_{i}")
                )

        output_state = gift_permbits(
            builder,
            state,
            f"test_permbits_{source}"
        )

        for row in range(4):
            for i in range(32):
                var = state[row][i]

                if i == source:
                    builder.cnf.append([var])
                else:
                    builder.cnf.append([-var])

        with Kissat404(
            bootstrap_with=builder.cnf.clauses
        ) as solver:

            assert solver.solve()
            model = solver.get_model()

        for row in range(4):
            expected_destination = GIFT_PERM[row][source]

            for destination in range(32):
                var = output_state[row][destination]

                if destination == expected_destination:
                    assert var in model
                else:
                    assert -var in model

def test_gift_add_round_key():
    builder = BasicFunctions()

    state = [
        [],
        [],
        [],
        []
    ]

    for row in range(4):
        for i in range(32):
            state[row].append(
                builder.var(f"state_{row}_{i}")
            )

    u = []
    v = []

    for i in range(32):
        u.append(
            builder.var(f"u_{i}")
        )

        v.append(
            builder.var(f"v_{i}")
        )

    state_values = [
        0x13579BDF,
        0xAAAAAAAA,
        0x0F0F0F0F,
        0x12345678
    ]

    u_value = 0x33333333
    v_value = 0x55555555

    round_constant = GIFT_ROUND_CONSTANTS[0]

    for row in range(4):
        for i in range(32):
            bit = (state_values[row] >> i) & 1
            var = state[row][i]

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

    for i in range(32):
        u_bit = (u_value >> i) & 1
        v_bit = (v_value >> i) & 1

        if u_bit == 1:
            builder.cnf.append([u[i]])
        else:
            builder.cnf.append([-u[i]])

        if v_bit == 1:
            builder.cnf.append([v[i]])
        else:
            builder.cnf.append([-v[i]])

    output_state = gift_add_round_key(
        builder,
        state,
        u,
        v,
        round_constant,
        "test_add_round_key"
    )

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    expected_values = [
        state_values[0],
        state_values[1] ^ v_value,
        state_values[2] ^ u_value,
        state_values[3] ^ (
            0x80000000 | round_constant
        )
    ]

    for row in range(4):
        output_value = 0

        for i in range(32):
            var = output_state[row][i]

            if var in model:
                output_value |= 1 << i

        assert output_value == expected_values[row]

def test_gift_key_schedule():
    builder = BasicFunctions()

    key_state = [
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        []
    ]

    for word in range(8):
        for i in range(16):
            key_state[word].append(
                builder.var(f"key_w{word}_{i}")
            )

    key_values = [
        0x0001,
        0x0203,
        0x0405,
        0x0607,
        0x0809,
        0x0A0B,
        0x0C0D,
        0x0E0F
    ]

    for word in range(8):
        for i in range(16):
            bit = (key_values[word] >> i) & 1
            var = key_state[word][i]

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

    u, v, new_key_state = gift_key_schedule(
        builder,
        key_state,
        "test_key_schedule"
    )

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    u_value = 0

    for i in range(32):
        if u[i] in model:
            u_value |= 1 << i

    v_value = 0

    for i in range(32):
        if v[i] in model:
            v_value |= 1 << i

    assert u_value == 0x04050607
    assert v_value == 0x0C0D0E0F

    expected_key_values = [
        0x4303,
        0xE0F0,
        0x0001,
        0x0203,
        0x0405,
        0x0607,
        0x0809,
        0x0A0B
    ]

    for word in range(8):
        output_value = 0

        for i in range(16):
            var = new_key_state[word][i]

            if var in model:
                output_value |= 1 << i

        assert output_value == expected_key_values[word]

def test_gift_round():
    builder = BasicFunctions()

    state = [
        [],
        [],
        [],
        []
    ]

    for row in range(4):
        for i in range(32):
            state[row].append(
                builder.var(f"round_state_{row}_{i}")
            )

    key_state = [
        [],
        [],
        [],
        [],
        [],
        [],
        [],
        []
    ]

    for word in range(8):
        for i in range(16):
            key_state[word].append(
                builder.var(f"round_key_w{word}_{i}")
            )

    state_values = [
        0x01234567,
        0x89ABCDEF,
        0x0F0F0F0F,
        0xF0F0F0F0
    ]

    key_values = [
        0x0001,
        0x0203,
        0x0405,
        0x0607,
        0x0809,
        0x0A0B,
        0x0C0D,
        0x0E0F
    ]

    for row in range(4):
        for i in range(32):
            bit = (state_values[row] >> i) & 1
            var = state[row][i]

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

    for word in range(8):
        for i in range(16):
            bit = (key_values[word] >> i) & 1
            var = key_state[word][i]

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

    output_state, new_key_state = gift_round(
        builder,
        state,
        key_state,
        GIFT_ROUND_CONSTANTS[0],
        "test_round"
    )

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    expected_subcells = [
        0,
        0,
        0,
        0
    ]

    for i in range(32):
        input_value = 0

        for row in range(4):
            bit = (state_values[row] >> i) & 1
            input_value |= bit << row

        output_value = GIFT_SBOX[input_value]

        for row in range(4):
            bit = (output_value >> row) & 1

            if bit == 1:
                expected_subcells[row] |= 1 << i

    expected_permbits = [
        0,
        0,
        0,
        0
    ]

    for row in range(4):
        for source in range(32):
            bit = (expected_subcells[row] >> source) & 1
            destination = GIFT_PERM[row][source]

            if bit == 1:
                expected_permbits[row] |= 1 << destination

    u_value = (
        key_values[2] << 16
    ) | key_values[3]

    v_value = (
        key_values[6] << 16
    ) | key_values[7]

    expected_state = [
        expected_permbits[0],
        expected_permbits[1] ^ v_value,
        expected_permbits[2] ^ u_value,
        expected_permbits[3] ^ (
            0x80000000 | GIFT_ROUND_CONSTANTS[0]
        )
    ]

    for row in range(4):
        output_value = 0

        for i in range(32):
            var = output_state[row][i]

            if var in model:
                output_value |= 1 << i

        assert output_value == expected_state[row]

    def rotate_right_16(value, amount):
        return (
            (value >> amount)
            |
            (value << (16 - amount))
        ) & 0xFFFF

    expected_key = [
        rotate_right_16(key_values[6], 2),
        rotate_right_16(key_values[7], 12),
        key_values[0],
        key_values[1],
        key_values[2],
        key_values[3],
        key_values[4],
        key_values[5]
    ]

    for word in range(8):
        output_value = 0

        for i in range(16):
            var = new_key_state[word][i]

            if var in model:
                output_value |= 1 << i

        assert output_value == expected_key[word]
