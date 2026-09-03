from pysat.formula import CNF, IDPool
from pysat.solvers import Kissat404


def xor(cnf: CNF, var_x: int, lits: list[int]) -> None:
    n = len(lits)
    total_rows = 2 ** n

    for i in range(total_rows):
        bits = []
        val = i

        for _ in range(n):
            bits.append(val % 2)
            val = val // 2

        expected_xor = 1 if sum(bits) % 2 != 0 else 0

        for x_val in [0, 1]:
            if x_val != expected_xor:
                clause = [var_x if x_val == 0 else -var_x]

                for lit, bit in zip(lits, bits):
                    clause.append(lit if bit == 0 else -lit)

                cnf.append(clause)


def eq_or(cnf: CNF, var_x: int, lits: list[int]) -> None:
    cnf.append([-var_x] + lits)

    for lit in lits:
        cnf.append([var_x, -lit])


def eq_and(cnf: CNF, var_x: int, lits: list[int]) -> None:
    cnf.append([var_x] + [-lit for lit in lits])

    for lit in lits:
        cnf.append([-var_x, lit])


def equals(cnf: CNF, var_a: int, var_b: int) -> None:
    cnf.append([var_a, -var_b])
    cnf.append([-var_a, var_b])


def test_xor():
    cnf = CNF()
    idp = IDPool()
    x = idp.id("x")
    a = idp.id("a")
    b = idp.id("b")
    c = idp.id("c")

    xor(cnf, x, [a, b, c])
    cnf.append([a])
    cnf.append([b])
    cnf.append([-c])

    with Kissat404(bootstrap_with=cnf.clauses) as solver:
        solution = solver.solve()
        model = solver.get_model()

        print(solution)
        print(model)


def test_eq_or():
    cnf = CNF()
    idp = IDPool()
    x = idp.id("x")
    a = idp.id("a")
    b = idp.id("b")

    eq_or(cnf, x, [a, b])
    cnf.append([-a])
    cnf.append([b])

    with Kissat404(bootstrap_with=cnf.clauses) as solver:
        solution = solver.solve()
        model = solver.get_model()

        print(solution)
        print(model)


def test_eq_and():
    cnf = CNF()
    idp = IDPool()
    x = idp.id("x")
    a = idp.id("a")
    b = idp.id("b")

    eq_and(cnf, x, [a, b])
    cnf.append([a])
    cnf.append([b])

    with Kissat404(bootstrap_with=cnf.clauses) as solver:
        solution = solver.solve()
        model = solver.get_model()

        print(solution)
        print(model)


def test_equals():
    cnf = CNF()
    idp = IDPool()
    a = idp.id("a")
    b = idp.id("b")

    equals(cnf, a, b)
    cnf.append([-b])

    with Kissat404(bootstrap_with=cnf.clauses) as solver:
        solution = solver.solve()
        model = solver.get_model()

        print(solution)
        print(model)


test_xor()
test_eq_or()
test_eq_and()
test_equals()

cnf = CNF()
idp = IDPool()

a_var = idp.id("a")
b_var = idp.id("b")
c_var = idp.id("c")
x_var = idp.id("x")

xor(cnf, x_var, [a_var, b_var, c_var])
eq_or(cnf, x_var, [a_var, b_var])
eq_and(cnf, x_var, [a_var, b_var])
equals(cnf, a_var, b_var)

print(cnf.clauses)

with Kissat404(bootstrap_with=cnf.clauses) as solver:
    solution = solver.solve()
    model = solver.get_model()

    print(solution)
    print(model)