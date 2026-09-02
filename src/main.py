from pysat.formula import CNF, IDPool
from pysat.solvers import Kissat404


def equals(cnf: CNF, var_a: int, var_b: int) -> None:
    cnf.append([var_a, -var_b])
    cnf.append([-var_a, var_b])


cnf = CNF()
idp = IDPool()

print(idp)

a_str = "a"
b_str = "b"

a_var = idp.id(a_str)
b_var = idp.id(b_str)

equals(cnf, a_var, b_var)
cnf.append([-b_var])

print(cnf.clauses)

with Kissat404(bootstrap_with=cnf.clauses) as solver:
    solution = solver.solve()
    model = solver.get_model()

    print(solution)
    print(model)
