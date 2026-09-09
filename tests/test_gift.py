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