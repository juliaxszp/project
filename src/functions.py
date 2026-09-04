from basics import *

#const
RC = [1, 3, 7, 14, 13, 11, 6, 12, 9, 2, 5, 10]
IC = [0, 1, 3, 7, 15, 14, 12, 8]
Sbox = [0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2]


def permutation(input_vars, perm):
    output_vars = []

    for i in range(len(perm)):
        input_var = input_vars[perm[i]]
        output_var = builder.var(f"out_{i}")

        builder.equals(output_var, input_var)

        output_vars.append(output_var)

    return output_vars

#czesc do addconstant
def xor_bits(self, x, y, b):   #b = y xor x, gdzie y to nowy bit
    if b == 0:  # b = 0, czyli y = x
        self.equals(x, y)
    else:  # b = 1, czyli y = not x
        self.equals_not([x, -y])

def xor_const(self, var_1, var_2, var_3):
    for i in range(len(var_1)):                              #zmiana z 4 bitów na dlugosc jednej zmiennej na potrzeby innych szyfrow
        self.xor_bits(var_1[i], var_2[i], var_3[i])