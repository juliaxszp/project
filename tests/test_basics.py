from src.basics import BasicFunctions
from pysat.solvers import Kissat404

def test_equals():
    print("TEST equals")

    tests = [
        (False, False, True),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ]

    for a_value, b_value, expected in tests:
        builder = BasicFunctions()

        a = builder.var("a")
        b = builder.var("b")

        builder.equals(a, b)

        if a_value:
            builder.cnf.append([a])
        else:
            builder.cnf.append([-a])

        if b_value:
            builder.cnf.append([b])
        else:
            builder.cnf.append([-b])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            result = solver.solve()

        assert result == expected

def test_equals_not():
    print("TEST equals")

    tests = [
        (False, False, False),
        (False, True, True),
        (True, False, True),
        (True, True, False),
    ]

    for a_value, b_value, expected in tests:
        builder = BasicFunctions()

        a = builder.var("a")
        b = builder.var("b")

        builder.equals_not(a, b)

        if a_value:
            builder.cnf.append([a])
        else:
            builder.cnf.append([-a])

        if b_value:
            builder.cnf.append([b])
        else:
            builder.cnf.append([-b])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            result = solver.solve()

        assert result == expected

def test_equal_or():
    print("TEST equal_or")

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
        builder = BasicFunctions()

        a = builder.var("a")
        b = builder.var("b")
        c = builder.var("c")

        builder.equal_or(a, [b, c])

        if a_value:
            builder.cnf.append([a])
        else:
            builder.cnf.append([-a])

        if b_value:
            builder.cnf.append([b])
        else:
            builder.cnf.append([-b])

        if c_value:
            builder.cnf.append([c])
        else:
            builder.cnf.append([-c])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            result = solver.solve()

        assert result == expected

def test_equal_and():
    print("TEST equal_and")

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
        builder = BasicFunctions()

        a = builder.var("a")
        b = builder.var("b")
        c = builder.var("c")

        builder.equal_and(a, [b, c])

        if a_value:
            builder.cnf.append([a])
        else:
            builder.cnf.append([-a])

        if b_value:
            builder.cnf.append([b])
        else:
            builder.cnf.append([-b])

        if c_value:
            builder.cnf.append([c])
        else:
            builder.cnf.append([-c])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            result = solver.solve()

        assert result == expected

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
        builder = BasicFunctions()

        a = builder.var("a")
        b = builder.var("b")
        c = builder.var("c")

        builder.xor([a, b, c])

        if a_value:
            builder.cnf.append([a])
        else:
            builder.cnf.append([-a])

        if b_value:
            builder.cnf.append([b])
        else:
            builder.cnf.append([-b])

        if c_value:
            builder.cnf.append([c])
        else:
            builder.cnf.append([-c])

        with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
            result = solver.solve()

        assert result == expected