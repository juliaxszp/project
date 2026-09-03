from basics import *
from functions import permutation
from pysat.solvers import Kissat404

builder = BasicFunctions()

# x = builder.var("x")
# y = builder.var("y")
# z = builder.var("z")
# w = builder.var("w")

# builder.equal_or(x, [y, z])

# print(builder.cnf.clauses)

a = builder.var("a")
b = builder.var("b")
c = builder.var("c")
d = builder.var("d")

result = permutation(
    [a, b, c, d],
    [2, 0, 3, 1]
)

print("output vars:", result)

builder.cnf.append([a])
builder.cnf.append([-b])
builder.cnf.append([-c])
builder.cnf.append([d])

with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
    if solver.solve():
        model = solver.get_model()
        print("model:", model)