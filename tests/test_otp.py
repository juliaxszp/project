from src.basics import BasicFunctions 
from src.otp import otp
from pysat.solvers import Kissat404


def test_otp():
    tests = [
        ([0], [0], [0]),
        ([0], [1], [1]),
        ([1], [0], [1]),
        ([1], [1], [0]),

        ([1, 0, 1, 1], [0, 1, 1, 0], [1, 1, 0, 1]),
        ([0, 0, 0, 0], [1, 1, 1, 1], [1, 1, 1, 1]),
        ([1, 1, 1, 1], [1, 1, 1, 1], [0, 0, 0, 0]),
    ]

    for plaintext_values, key_values, expected in tests:
        builder = BasicFunctions()

        plaintext_vars =[]
        key_vars = []

        for i in range(len(plaintext_values)):
            plaintext_vars.append(builder.var(f"plaintext_{i}"))
            key_vars.append(builder.var(f"key_{i}"))


        ciphertext_vars = otp(builder, plaintext_vars, key_vars)

        for var, value in zip(plaintext_vars, plaintext_values):
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

        ciphertext_values = []

        for var in ciphertext_vars:
            if var in model:
                ciphertext_values.append(1)
            else:
                ciphertext_values.append(0)

        assert ciphertext_values == expected
            