from pysat.formula import CNF, IDPool
from itertools import product



class Builder:
    def __init__(self):
        self.cnf = CNF()
        self.idp = IDPool()

    def var(self, name):
        return self.idp.id(name)


    
class BasicFunctions(Builder):
    def equals(self, var_a, var_b):
            self.cnf.append([var_a, -var_b])
            self.cnf.append([-var_a, var_b])

    def equal_and(self, var_a, vars:list) -> None:
        for var in vars:
            self.cnf.append([-var_a, var])

        self.cnf.append([var_a] + [-var for var in vars])

    def equal_or(self, var_a, vars: list) -> None:
        for var in vars:
            self.cnf.append([var_a, -var])

        self.cnf.append([-var_a] + [var for var in vars])


    def xor(self, vars: list) -> None:
        n = len(vars)
        for values in product([0, 1], repeat=n):
            if values.count(1) % 2 == 1:
                clause = []

                for var, value in zip(vars, values):
                    if value == 0:
                        clause.append(var)
                    else:
                        clause.append(-var)

                self.cnf.append(clause)
