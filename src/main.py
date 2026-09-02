
from pysat.formula import CNF, IDPool
from pysat.solvers import Kissat404
from itertools import product


def equals(cnf: CNF, var_a: int, var_b: int) -> None:
    cnf.append([var_a, -var_b])
    cnf.append([-var_a, var_b])


cnf = CNF()
idp = IDPool()



def equal_and(cnf: CNF, var_a: int, vars: list[int]) -> None:
    for var in vars:
        cnf.append([-var_a, var])

    cnf.append([var_a] + [-var for var in vars])


def equal_or(cnf: CNF, var_a: int, vars: list[int]) -> None:
    for var in vars:
        cnf.append([var_a, -var])

    cnf.append([-var_a] + [var for var in vars])

a_str = "a"
b_str = "b"
c_str = "c"

a_var = idp.id(a_str)
b_var = idp.id(b_str)
c_var = idp.id(c_str)

equal_or(cnf, a_var, [b_var, c_var])

print(cnf.clauses)

with Kissat404(bootstrap_with=cnf.clauses) as solver:
    while solver.solve():
        model = solver.get_model()
        print(model)

        solver.add_clause([-x for x in model])  



def xor(cnf: CNF, vars: list[int]) -> None:
    n = len(vars)
    for values in product([0, 1], repeat=n):
        if values.count(1) % 2 == 1:
            clause = []

            for var, value in zip(vars, values):
                if value == 0:
                    clause.append(var)
                else:
                    clause.append(-var)

            cnf.append(clause)


def test_equals():
    cnf = CNF()

    equals(cnf, 1, 2)

    tests = [
        ([-1, -2], True),    
        ([-1,  2], False),   
        ([ 1, -2], False),  
        ([ 1,  2], True)     
    ]

    for variables, expected in tests:
        with Kissat404(bootstrap_with=cnf.clauses) as solver:
            for literal in variables:
                solver.add_clause([literal])

            assert solver.solve() == expected

def test_equal_and():
    cnf = CNF()

    equal_and(cnf, 1, [2, 3])

    tests = [
        ([-1, -2, -3], True),    
        ([-1,  2, -3], True),   
        ([-1, -2,  3], True),  
        ([-1,  2,  3], False),  
        ([ 1, -2, -3], False),  
        ([ 1,  2, -3], False),  
        ([ 1, -2,  3], False),  
        ([ 1,  2,  3], True)     
    ]

    for variables, expected in tests:
        with Kissat404(bootstrap_with=cnf.clauses) as solver:
            for literal in variables:
                solver.add_clause([literal])

            assert solver.solve() == expected

def test_equal_or():
    cnf = CNF()

    equal_or(cnf, 1, [2, 3])

    tests = [
        ([-1, -2, -3], True),    
        ([-1,  2, -3], False),   
        ([-1, -2,  3], False),  
        ([-1,  2,  3], False),  
        ([ 1, -2, -3], False),  
        ([ 1,  2, -3], True),  
        ([ 1, -2,  3], True),  
        ([ 1,  2,  3], True)     
    ]

    for variables, expected in tests:
        with Kissat404(bootstrap_with=cnf.clauses) as solver:
            for literal in variables:
                solver.add_clause([literal])

            assert solver.solve() == expected

def test_xor():
    cnf = CNF()

    xor(cnf, [1, 2, 3])

    tests = [
        ([-1, -2, -3], True),    
        ([-1,  2, -3], False),   
        ([-1, -2,  3], False),  
        ([-1,  2,  3], True),  
        ([ 1, -2, -3], False),  
        ([ 1,  2, -3], True),  
        ([ 1, -2,  3], True),  
        ([ 1,  2,  3], False)     
    ]

    for variables, expected in tests:
        with Kissat404(bootstrap_with=cnf.clauses) as solver:
            for literal in variables:
                solver.add_clause([literal])

            assert solver.solve() == expected
