from pysat.formula import CNF, IDPool
from pysat.solvers import Kissat404


def equals(cnf: CNF, var_a: int, var_b: int) -> None:
    cnf.append([var_a, -var_b])
    cnf.append([-var_a, var_b])

def equals_or(cnf: CNF, var_a: int, vars: list[int]) -> None:
    cnf.append([-var_a], + vars)

    for var in vars:
        cnf.append([var_a, -var])

cnf = CNF()
idp = IDPool()

print(idp)

a_str = "a"
b_str = "b"
c_str = "c"

a_var = idp.id(a_str)
b_var = idp.id(b_str)
c_var = idp.id(c_str)

equals(cnf, a_var, b_var)
cnf.append([-b_var])

print(cnf.clauses)

with Kissat404(bootstrap_with=cnf.clauses) as solver:
    solution = solver.solve()
    model = solver.get_model()

    print(solution)
    print(model)
