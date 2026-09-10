from src.basics import BasicFunctions
from src.gift_cofb import cofb_pad
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