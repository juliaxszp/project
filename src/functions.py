from basics import *
from pysat.solvers import Kissat404

def permutation(input_vars, perm):
    output_vars = []

    for i in range(len(perm)):
        input_var = input_vars[perm[i]]
        output_var = builder.var(f"out_{i}")

        builder.equals(output_var, input_var)

        output_vars.append(output_var)

    return output_vars