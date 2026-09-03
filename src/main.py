from basics import BasicFunctions
from functions import permutation
from pysat.solvers import Kissat404

builder = BasicFunctions()

a = builder.var("a")
b = builder.var("b")
c = builder.var("c")
d = builder.var("d")

output = permutation(
    builder,
    [a, b, c, d],
    [2, 0, 3, 1]
)

print("Zmienne wejściowe:", [a, b, c, d])
print("Zmienne wyjściowe:", output)

builder.cnf.append([a])
builder.cnf.append([-b])
builder.cnf.append([-c])
builder.cnf.append([d])

with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:

    if solver.solve():
        model = solver.get_model()

        print("Model:", model)

        output_values = []

        for var in output:
            if var in model:
                output_values.append(1)
            else:
                output_values.append(0)

        print("Wejście:     ", [1, 0, 0, 1])
        print("Permutacja:  ", [2, 0, 3, 1])
        print("Wyjście:     ", output_values)

        assert output_values == [0, 1, 1, 0]

        print("PERMUTACJA DZIAŁA POPRAWNIE")

    else:
        print("UNSAT - coś jest nie tak")