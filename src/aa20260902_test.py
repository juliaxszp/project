from pysat.formula import CNF, IDPool
from pysat.solvers import Kissat404

from aa20260902 import equals, sand, sor, sxor


def test_equals():
    cnf = CNF()
    idp = IDPool()

    a = idp.id("a")
    b = idp.id("b")

    equals(cnf, a, b)

    cnf.append([a])
    cnf.append([b])

    with Kissat404(bootstrap_with=cnf.clauses) as solver:
        assert solver.solve() is True


def test_and():
    cnf = CNF()
    idp = IDPool()

    a = idp.id("a")
    b = idp.id("b")
    c = idp.id("c")

    sand(cnf, a, [b, c], 2)

    cnf.append([a])
    cnf.append([b])
    cnf.append([c])

    with Kissat404(bootstrap_with=cnf.clauses) as solver:
        assert solver.solve() is True


def test_or():
    cnf = CNF()
    idp = IDPool()

    a = idp.id("a")
    b = idp.id("b")
    c = idp.id("c")

    sor(cnf, a, [b, c], 2)

    cnf.append([a])
    cnf.append([-b])
    cnf.append([c])

    with Kissat404(bootstrap_with=cnf.clauses) as solver:
        assert solver.solve() is True


def test_xor():
    cnf = CNF()
    idp = IDPool()

    a = idp.id("a")
    b = idp.id("b")
    c = idp.id("c")

    sxor(cnf, a, [b, c], 2)

    cnf.append([a])
    cnf.append([-b])
    cnf.append([c])

    with Kissat404(bootstrap_with=cnf.clauses) as solver:
        assert solver.solve() is True