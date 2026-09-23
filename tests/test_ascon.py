from src.ascon import *
from pysat.solvers import Kissat404


def test_add_constant():

    cases = [
        ([0] * 64, 0, [0] * 64),
        ([0] * 64, 1, [1] + [0] * 63),
        ([1] * 64, 0, [1] * 64),
        ([1] * 64, (2 ** 64) - 1, [0] * 64),
        ([1, 0] * 32, 0b11, [0, 1] + [1, 0] * 31),
        ([1, 0] * 32, 0x6666666666666666, [1, 1, 0, 0, 1, 1, 0, 0] * 8)
    ]

    for S2_values, constant, expected in cases:
        builder = BasicFunctions()

        S2 = []
        for i in range(64):
            var = builder.var(f"S2_{i}")
            S2.append(var)
        
            
        output = add_constant(builder, S2, constant)

        for var, value in zip(S2, S2_values):
            if value == 0:
                builder.cnf.append([-var])
            else:
                builder.cnf.append([var])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            assert solver.solve()
            model = solver.get_model()
                

        output_values = []

        for var in(output):
            if var in model:
                value = 1
            else:
                value = 0
            output_values.append(value)

        assert output_values == expected






def test_S_box():

    expected = [
         4, 11, 31, 20, 26, 21, 9, 2,
         27, 5, 8, 18, 29, 3, 6, 28, 
         30, 19, 7, 14, 0, 13, 17, 24,
         16, 12, 1, 25, 22, 10, 15, 23

    ]

    for input_value in range(32):
        builder = BasicFunctions()
        S = []
        for i in range(5):
            
            var = builder.var(f"S_{i}")
            S.append(var)

            bit = (input_value >> (4 - i)) & 1

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        out = S_box(builder, S[0], S[1], S[2], S[3], S[4])
        expected_bits = []
        wyniki_wartosci = []

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            assert solver.solve()
            model = solver.get_model()


        for i in range(5):
            expected_bit = (expected[input_value] >> (4 - i)) & 1
            expected_bits.append(expected_bit)

            if out[i] in model:
                wartosc = 1
            else:
                wartosc = 0
            wyniki_wartosci.append(wartosc)

        print(input_value, wyniki_wartosci, expected_bits)
        assert wyniki_wartosci == expected_bits

               


def test_S_box_64():
    expected = [
    4, 11, 31, 20, 26, 21, 9, 2,
    27, 5, 8, 18, 29, 3, 6, 28,
    30, 19, 7, 14, 0, 13, 17, 24,
    16, 12, 1, 25, 22, 10, 15, 23
    ]
    
    builder = BasicFunctions()
    S0 = []
    S1 = []
    S2 = []
    S3 = []
    S4 = []

    for i in range(64):
        S0.append(builder.var(f"S0_{i}"))
        S1.append(builder.var(f"S1_{i}"))
        S2.append(builder.var(f"S2_{i}"))
        S3.append(builder.var(f"S3_{i}"))
        S4.append(builder.var(f"S4_{i}"))

    output = S_box_64(
        builder,
        S0,
        S1,
        S2,
        S3,
        S4
    )

    input_values = [i % 32 for i in range(64)]

    for i in range(64):
        input_value = input_values[i]

        for j, S in enumerate([S0, S1, S2, S3, S4]):
            bit = (input_value >> (4 - j)) & 1
            if bit == 1:
                builder.cnf.append([S[i]])
            else:
                builder.cnf.append([-S[i]])

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        assert solver.solve()
        model = solver.get_model()



    S0_output, S1_output, S2_output, S3_output, S4_output = output

    for i in range(64):
        wynik = []

        if S0_output[i] in model:
            wynik.append(1)
        else:
            wynik.append(0)

        if S1_output[i] in model:
            wynik.append(1)
        else:
            wynik.append(0)

        if S2_output[i] in model:
            wynik.append(1)
        else:
            wynik.append(0)

        if S3_output[i] in model:
            wynik.append(1)
        else:
            wynik.append(0)

        if S4_output[i] in model:
            wynik.append(1)
        else:
            wynik.append(0)


        expected_value = expected[input_values[i]]
        expected_bits = []

        for j in range(5):
            bit = (expected_value >> (4 - j)) & 1
            expected_bits.append(bit)

        assert wynik == expected_bits




def test_Linear_Diffusion():

    cases = [
        ([1] + [0] * 63, 19, 28),
        ([0] * 64, 19, 28),
        ([1] * 64, 19, 28),
        ([0] * 63 + [1], 19, 28),
        ([1, 0] * 32, 19, 28),
        ([0, 1] * 32, 19, 28),
        ([1] + [0] * 63, 1, 2),
        ([1] + [0] * 63, 32, 63),
    ]

    for S_values, a, b in cases:

        builder = BasicFunctions()

        S = []

        for i in range(64):
            var = builder.var(f"S_{i}")
            S.append(var)

        output = Linear_Diffusion(
            builder,
            S,
            a,
            b
        )

        for var, value in zip(S, S_values):
            if value == 0:
                builder.cnf.append([-var])
            else:
                builder.cnf.append([var])

        with Kissat404(
            bootstrap_with=builder.cnf.clauses
        ) as solver:

            assert solver.solve()
            model = solver.get_model()

        output_values = []

        for var in output:
            if model[var - 1] > 0:
                output_values.append(1)
            else:
                output_values.append(0)

        expected = []

        for i in range(64):
            value = (
                S_values[i]
                ^ S_values[(i + a) % 64]
                ^ S_values[(i + b) % 64]
            )

            expected.append(value)

        assert output_values == expected

