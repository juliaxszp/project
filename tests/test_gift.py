from src.basics import BasicFunctions
from src.gift import gift_subcells, GIFT_SBOX
from pysat.solvers import Kissat404

def test_gift_subcells():
    for input_value in range(16):
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

        input_bits = []

        for i in range(4):
            bit = (input_value >> i) & 1
            input_bits.append(bit)

        for row in range(4):
            var = state[row][0]
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

        output_bits = []

        for row in range(4):
            var = output_state[row][0]

            if var in model:
                output_bits.append(1)
            else:
                output_bits.append(0)

        output_value = 0

        for i, bit in enumerate(output_bits):
            output_value |= bit << i

        assert output_value == GIFT_SBOX[input_value]