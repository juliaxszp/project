from src.basics import BasicFunctions
from src.functions import permutation, xor_bits, xor_const
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