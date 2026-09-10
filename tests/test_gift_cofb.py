from src.basics import BasicFunctions
from src.gift_cofb import *
from pysat.solvers import Kissat404

def test_cofb_pad_full_block():
    builder = BasicFunctions()

    data = []

    for i in range(128):
        data.append(
            builder.var(f"data_{i}")
        )

    blocks = cofb_pad(
        builder,
        data,
        prefix="test_full"
    )

    assert len(blocks) == 1
    assert len(blocks[0]) == 128

    assert blocks[0] == data

def test_cofb_pad_partial_block():
    builder = BasicFunctions()

    data = []

    for i in range(10):
        data.append(
            builder.var(f"data_{i}")
        )

    blocks = cofb_pad(
        builder,
        data,
        prefix="test_partial"
    )

    assert len(blocks) == 1
    assert len(blocks[0]) == 128

    assert blocks[0][:10] == data

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    assert blocks[0][10] in model

    for i in range(11, 128):
        assert -blocks[0][i] in model

def test_cofb_pad_empty():
    builder = BasicFunctions()

    data = []

    blocks = cofb_pad(
        builder,
        data,
        prefix="test_empty"
    )

    assert len(blocks) == 1
    assert len(blocks[0]) == 128

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        assert solver.solve()
        model = solver.get_model()

    assert blocks[0][0] in model

    for i in range(1, 128):
        assert -blocks[0][i] in model

def test_cofb_g():
    test_positions = [
        (0, 127),
        (1, 64),
        (63, 126),
        (64, 0),
        (65, 1),
        (127, 63)
    ]

    for source, expected_destination in test_positions:
        builder = BasicFunctions()

        y = []

        for i in range(128):
            var = builder.var(f"y_{source}_{i}")
            y.append(var)

            if i == source:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        output = cofb_g(
            builder,
            y,
            f"test_g_{source}"
        )

        with Kissat404(
            bootstrap_with=builder.cnf.clauses
        ) as solver:

            assert solver.solve()
            model = solver.get_model()

        for i in range(128):
            if i == expected_destination:
                assert output[i] in model
            else:
                assert -output[i] in model

def test_cofb_double():
    test_cases = [
        (
            0x0123456789ABCDEF,
            0x02468ACF13579BDE
        ),
        (
            0x8000000000000000,
            0x000000000000001B
        )
    ]

    for case_index, (
        input_value,
        expected_value
    ) in enumerate(test_cases):

        builder = BasicFunctions()

        l = []

        for i in range(64):
            var = builder.var(
                f"double_{case_index}_{i}"
            )

            l.append(var)

            bit = (
                input_value >> (63 - i)
            ) & 1

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        output = cofb_double(
            builder,
            l,
            f"test_double_{case_index}"
        )

        with Kissat404(
            bootstrap_with=builder.cnf.clauses
        ) as solver:

            assert solver.solve()
            model = solver.get_model()

        output_value = 0

        for i in range(64):
            output_value <<= 1

            if output[i] in model:
                output_value |= 1

        assert output_value == expected_value

def test_cofb_triple():
    test_cases = [
        (
            0x0123456789ABCDEF,
            0x0365CFA89AFC5631
        ),
        (
            0x8000000000000000,
            0x800000000000001B
        )
    ]

    for case_index, (
        input_value,
        expected_value
    ) in enumerate(test_cases):

        builder = BasicFunctions()

        l = []

        for i in range(64):
            var = builder.var(
                f"triple_{case_index}_{i}"
            )

            l.append(var)

            bit = (
                input_value >> (63 - i)
            ) & 1

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

        output = cofb_triple(
            builder,
            l,
            f"test_triple_{case_index}"
        )

        with Kissat404(
            bootstrap_with=builder.cnf.clauses
        ) as solver:

            assert solver.solve()
            model = solver.get_model()

        output_value = 0

        for i in range(64):
            output_value <<= 1

            if output[i] in model:
                output_value |= 1

        assert output_value == expected_value