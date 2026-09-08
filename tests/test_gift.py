from src.basics import BasicFunctions
from src.gift import gift_subcells, GIFT_SBOX, gift_permbits, GIFT_PERM
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