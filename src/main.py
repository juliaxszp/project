from basics import *

builder = BasicFunctions()

x = builder.var("x")
y = builder.var("y")
z = builder.var("z")
w = builder.var("w")

builder.equal_or(x, [y, z])

print(builder.cnf.clauses)