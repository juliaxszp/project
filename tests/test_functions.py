from src.basics import BasicFunctions
from src.functions import *
from pysat.solvers import Kissat404

def test_permutation():
    tests = [
        (
            [1, 0, 0, 1],
            [2, 0, 3, 1],
            [0, 1, 1, 0]
        ),

        (
            [1, 0, 1, 0],
            [0, 1, 2, 3],
            [1, 0, 1, 0]
        ),

        (
            [1, 0, 0, 1],
            [3, 2, 1, 0],
            [1, 0, 0, 1]
        ),

        (
            [1, 0, 1, 1, 0, 0, 1, 0],
            [6, 2, 7, 0, 5, 1, 3, 4],
            [1, 1, 0, 1, 0, 0, 1, 0]
        ),
    ]

    for input_values, perm, expected in tests:
        builder = BasicFunctions()

        input_vars = []

        for i in range(len(input_values)):
            var = builder.var(f"in_{i}")
            input_vars.append(var)

        result = permutation(
            builder,
            input_vars,
            perm
        )

        for var, value in zip(input_vars, input_values):
            if value == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            assert solver.solve()
            model = solver.get_model()

        output_values = []

        for var in result:
            if var in model:
                output_values.append(1)
            else:
                output_values.append(0)

        assert output_values == expected

def test_xor_bits():
    tests = [
        (False, 0, False),
        (True,  0, True),
        (False, 1, True),
        (True,  1, False),
    ]

    for x_value, constant, expected_y in tests:
        builder = BasicFunctions()

        x = builder.var("x")
        y = builder.var("y")

        xor_bits(builder, x, y, constant)

        if x_value:
            builder.cnf.append([x])
        else:
            builder.cnf.append([-x])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            assert solver.solve()
            model = solver.get_model()

        if y in model:
            y_value = True
        else:
            y_value = False

        assert y_value == expected_y

def test_xor_const():
    tests = [
        (
            [1, 0, 1, 1],
            [0, 1, 1, 0],
            [1, 1, 0, 1]
        ),
        (
            [0, 0, 0, 0],
            [1, 1, 1, 1],
            [1, 1, 1, 1]
        ),
        (
            [1, 1, 1, 1],
            [1, 1, 1, 1],
            [0, 0, 0, 0]
        ),
        (
            [1, 0, 1, 0],
            [0, 0, 0, 0],
            [1, 0, 1, 0]
        ),
    ]

    for input_values, constant, expected in tests:
        builder = BasicFunctions()

        input_vars = []
        output_vars = []

        for i in range(len(input_values)):
            input_vars.append(builder.var(f"in_{i}"))
            output_vars.append(builder.var(f"out_{i}"))

        xor_const(
            builder,
            input_vars,
            output_vars,
            constant
        )

        for var, value in zip(input_vars, input_values):
            if value == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            assert solver.solve()
            model = solver.get_model()

        output_values = []

        for var in output_vars:
            if var in model:
                output_values.append(1)
            else:
                output_values.append(0)

        assert output_values == expected

def test_add_round_key():
    tests = [
        ([0], [0], [0]),
        ([0], [1], [1]),
        ([1], [0], [1]),
        ([1], [1], [0]),

        ([1, 0, 1, 1], [0, 1, 1, 0], [1, 1, 0, 1]),
        ([0, 0, 0, 0], [1, 1, 1, 1], [1, 1, 1, 1]),
        ([1, 1, 1, 1], [1, 1, 1, 1], [0, 0, 0, 0]),
    ]

    for state_values, key_values, expected in tests:
        builder = BasicFunctions()

        state_vars = []
        key_vars = []

        for i in range(len(state_values)):
            state_vars.append(builder.var(f"state_{i}"))
            key_vars.append(builder.var(f"key_{i}"))

        output_vars = add_round_key(
            builder,
            state_vars,
            key_vars
        )

        for var, value in zip(state_vars, state_values):
            if value == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        for var, value in zip(key_vars, key_values):
            if value == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            assert solver.solve()
            model = solver.get_model()

        output_values = []

        for var in output_vars:
            if var in model:
                output_values.append(1)
            else:
                output_values.append(0)

        assert output_values == expected

def test_sbox():
    tests = [
        (
            2,
            2,
            [2, 0, 3, 1]
        ),
        (
            3,
            3,
            [5, 2, 7, 1, 0, 6, 3, 4]
        ),
        (
            4,
            4,
            [
                0x9, 0x4, 0xA, 0xB,
                0xD, 0x1, 0x8, 0x5,
                0x6, 0x2, 0x0, 0x3,
                0xC, 0xE, 0xF, 0x7
            ]
        ),
    ]

    for input_size, output_size, sbox_table in tests:

        for input_value in range(2 ** input_size):
            builder = BasicFunctions()

            input_vars = []

            for i in range(input_size):
                input_vars.append(
                    builder.var(f"input_{i}")
                )

            output_vars = sbox(
                builder,
                input_vars,
                sbox_table,
                output_size,
                f"sbox_{input_size}_{input_value}"
            )

            input_bits = []

            for i in range(input_size):
                bit = (input_value >> i) & 1
                input_bits.append(bit)

            for var, bit in zip(input_vars, input_bits):
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

            for var in output_vars:
                if var in model:
                    output_bits.append(1)
                else:
                    output_bits.append(0)

            output_value = 0

            for i, bit in enumerate(output_bits):
                output_value |= bit << i

            expected_output = sbox_table[input_value]

            assert output_value == expected_output




def test_rotate_right():
    tests = [
        ([0, 1, 2, 3], 0, [0, 1, 2, 3]),
        ([0, 1, 2, 3], 1, [3, 0, 1, 2]),
        ([0, 1, 2, 3], 2, [2, 3, 0, 1]),
        ([0, 1, 2, 3], 3, [1, 2, 3, 0]),
        ([0, 1, 2, 3], 4, [0, 1, 2, 3]),
        ([0, 1, 2, 3], 5, [3, 0, 1, 2]),
        ([0, 1, 2, 3, 4, 5, 6, 7], 3, [5, 6, 7, 0, 1, 2, 3, 4]),

        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 5,
        [7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5, 6]),

        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20], 7,
         [14, 15, 16, 17, 18, 19, 20, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]),

         (list(range(64)), 13,
         list(range(51, 64)) + list(range(51))),

    ]

    for input_values, n, expected in tests:
        result = rotate_right(input_values, n)
        assert result == expected
