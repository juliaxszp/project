from pysat.formula import CNF, IDPool
from pysat.solvers import Kissat404
from itertools import product

def equals(cnf: CNF, var_a: int, var_b: int) -> None:
    cnf.append([var_a, -var_b])
    cnf.append([-var_a, var_b])

def equals_or(cnf: CNF, var_a: int, variables: list[int]) -> None:
    for var in variables:
        cnf.append([var_a, -var])

    cnf.append([-var_a] + variables)

def equals_and(cnf: CNF, var_a: int, variables: list[int]) -> None:
    for var in variables:
        cnf.append([-var_a, var])

    cnf.append([var_a] + [-var for var in variables])

def xor(cnf: CNF, variables: list[int]) -> None:
    for values in product([False, True], repeat=len(variables)):
        if sum(values) % 2 == 0:
            clause = []

            for var, value in zip(variables, values):
                if value:
                    clause.append(-var)
                else:
                    clause.append(var)

            cnf.append(clause)

def test_equals():
    print("TEST equals")

    tests = [
        (False, False, True),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ]

    for a_value, b_value, expected in tests:
        cnf = CNF()
        idp = IDPool()

        a = idp.id("a")
        b = idp.id("b")

        equals(cnf, a, b)

        if a_value:
            cnf.append([a])
        else:
            cnf.append([-a])

        if b_value:
            cnf.append([b])
        else:
            cnf.append([-b])

        with Kissat404(bootstrap_with=cnf.clauses) as solver:
            result = solver.solve()

        print(
            "a =", a_value,
            "b =", b_value,
            "| wynik =", result,
            "| oczekiwano =", expected
        )

    print()

def test_equals_or():
    print("TEST equals_or")

    tests = [
        (False, False, False, True),
        (False, False, True, False),
        (False, True, False, False),
        (False, True, True, False),

        (True, False, False, False),
        (True, False, True, True),
        (True, True, False, True),
        (True, True, True, True),
    ]

    for a_value, b_value, c_value, expected in tests:
        cnf = CNF()
        idp = IDPool()

        a = idp.id("a")
        b = idp.id("b")
        c = idp.id("c")

        equals_or(cnf, a, [b, c])

        if a_value:
            cnf.append([a])
        else:
            cnf.append([-a])

        if b_value:
            cnf.append([b])
        else:
            cnf.append([-b])

        if c_value:
            cnf.append([c])
        else:
            cnf.append([-c])

        with Kissat404(bootstrap_with=cnf.clauses) as solver:
            result = solver.solve()

        print(
            "a =", a_value,
            "b =", b_value,
            "c =", c_value,
            "| wynik =", result,
            "| oczekiwano =", expected
        )

    print()

def test_equals_and():
    print("TEST equals_and")

    tests = [
        (False, False, False, True),
        (False, False, True, True),
        (False, True, False, True),
        (False, True, True, False),

        (True, False, False, False),
        (True, False, True, False),
        (True, True, False, False),
        (True, True, True, True),
    ]

    for a_value, b_value, c_value, expected in tests:
        cnf = CNF()
        idp = IDPool()

        a = idp.id("a")
        b = idp.id("b")
        c = idp.id("c")

        equals_and(cnf, a, [b, c])

        if a_value:
            cnf.append([a])
        else:
            cnf.append([-a])

        if b_value:
            cnf.append([b])
        else:
            cnf.append([-b])

        if c_value:
            cnf.append([c])
        else:
            cnf.append([-c])

        with Kissat404(bootstrap_with=cnf.clauses) as solver:
            result = solver.solve()

        print(
            "a =", a_value,
            "b =", b_value,
            "c =", c_value,
            "| wynik =", result,
            "| oczekiwano =", expected
        )

    print()

def test_xor():
    print("TEST xor")

    tests = [
        (False, False, False, False),
        (False, False, True, True),
        (False, True, False, True),
        (False, True, True, False),

        (True, False, False, True),
        (True, False, True, False),
        (True, True, False, False),
        (True, True, True, True),
    ]

    for a_value, b_value, c_value, expected in tests:
        cnf = CNF()
        idp = IDPool()

        a = idp.id("a")
        b = idp.id("b")
        c = idp.id("c")

        xor(cnf, [a, b, c])

        if a_value:
            cnf.append([a])
        else:
            cnf.append([-a])

        if b_value:
            cnf.append([b])
        else:
            cnf.append([-b])

        if c_value:
            cnf.append([c])
        else:
            cnf.append([-c])

        with Kissat404(bootstrap_with=cnf.clauses) as solver:
            result = solver.solve()

        print(
            "a =", a_value,
            "b =", b_value,
            "c =", c_value,
            "| wynik =", result,
            "| oczekiwano =", expected
        )

    print()

cnf = CNF()
idp = IDPool()

#print(idp)

a_str = "a"
b_str = "b"
c_str = "c"

a_var = idp.id(a_str)
b_var = idp.id(b_str)
c_var = idp.id(c_str)

#equals(cnf, a_var, b_var)
#cnf.append([-b_var])

equals_or(cnf, a_var, [b_var, c_var])

#equals_and(cnf, a_var, [b_var, c_var])

#xor(cnf, [a_var, b_var, c_var])

test_equals()
test_equals_or()
test_equals_and()
test_xor()

print(cnf.clauses)

models = []

while True:
    with Kissat404(bootstrap_with=cnf.clauses) as solver:
        if not solver.solve():
            break

        model = solver.get_model()
        models.append(model)

        blocking_clause = [-lit for lit in model]
        cnf.append(blocking_clause)

for model in models:
    print(model)