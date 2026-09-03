from src.functions import equals, equals_or, equals_and, xor
from pysat.solvers import Kissat404
from pysat.formula import CNF, IDPool

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

test_equals()
test_equals_or()
test_equals_and()
test_xor()