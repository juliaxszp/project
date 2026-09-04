from src.basics import BasicFunctions
from src.functions import permutation
from pysat.solvers import Kissat404

def test_permutation():
    builder = BasicFunctions()

    a = builder.var("a")
    b = builder.var("b")
    c = builder.var("c")
    d = builder.var("d")

    result = permutation(
        builder,
        [a, b, c, d],
        [2, 0, 3, 1]
    )

    builder.cnf.append([a])
    builder.cnf.append([-b])
    builder.cnf.append([-c])
    builder.cnf.append([d])

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        assert solver.solve()
        model = solver.get_model()

    print(model)

    output_values = []

    for var in result:
        if var in model:
            output_values.append(1)
        else:
            output_values.append(0)

    print("output:", output_values)

    assert output_values == [0, 1, 1, 0]