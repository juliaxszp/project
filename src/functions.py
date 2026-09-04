from basics import *

#const
RC = [1, 3, 7, 14, 13, 11, 6, 12, 9, 2, 5, 10]
IC = [0, 1, 3, 7, 15, 14, 12, 8]
Sboxphoton = [0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2]
GF16photon = [0x2, 0x4, 0x2, 0xB, 0x2, 0x8, 0x5, 0x6]

def permutation(input_vars, perm):
    output_vars = []

    for i in range(len(perm)):
        input_var = input_vars[perm[i]]
        output_var = builder.var(f"out_{i}")

        builder.equals(output_var, input_var)

        output_vars.append(output_var)

    return output_vars

#czesc do addconstant
def xor_bits(Builder, x, y, b):   #b = y xor x, gdzie y to nowy bit
    if b == 0:  # b = 0, czyli y = x
        Builder.equals(x, y)
    else:  # b = 1, czyli y = not x
        Builder.equals_not([x, y])

def xor_const(Builder, var_1, var_2, var_3):
    for i in range(len(var_1)):                              #zmiana z 4 bitów na dlugosc jednej zmiennej na potrzeby innych szyfrow
        Builder.xor_bits(var_1[i], var_2[i], var_3[i])

#czesc do mixcolumns dla photon (korzysta z macierzy w GF16)
def gf16_mul(Builder, var_a, var_b, prefix):           #mnozenie w GF16 pojedynczego nibble, zredukowanie o wielomian x^4+x+1
    temp = []
    for i in range(4):
        for j in range(4):
            t = Builder.var(f"{prefix}_temp_{i}{j}")
            Builder.equal_and(t, [var_a[i], var_b[j]])
            temp.append(t)

    c0 = Builder.var(f"{prefix}_c0")
    c1 = Builder.var(f"{prefix}_c1")
    c2 = Builder.var(f"{prefix}_c2")
    c3 = Builder.var(f"{prefix}_c3")
    c4 = Builder.var(f"{prefix}_c4")
    c5 = Builder.var(f"{prefix}_c5")
    c6 = Builder.var(f"{prefix}_c6")

    Builder.equals(c0, temp[0])
    Builder.xor([c1, temp[1], temp[4]])
    Builder.xor([c2, temp[2], temp[5], temp[8]])
    Builder.xor([c3, temp[3], temp[6], temp[9], temp[12]])
    Builder.xor([c4, temp[7], temp[10], temp[13]])
    Builder.xor([c5, temp[11], temp[14]])
    Builder.equals(c6, temp[15])          #mamy za duzo bitow, wiec redukcja

    r0 = Builder.var(f"{prefix}_r0")
    r1 = Builder.var(f"{prefix}_r1")
    r2 = Builder.var(f"{prefix}_r2")
    r3 = Builder.var(f"{prefix}_r3")

    Builder.xor([r0, c0, c4])
    Builder.xor([r1, c1, c4, c5])
    Builder.xor([r2, c2, c5, c6])
    Builder.xor([r3, c3, c6])

    return [r0, r1, r2, r3]


def gf16_const_mult(Builder, var_a):
    result = []

    for i in range(8):
        constant = GF16photon[i]
        constant_bits = [(constant >> j) & 1 for j in range(4)]
        var_b=[]

        for j in range(4):
            c = Builder.var(f"constant_{i}_{j}")

            if constant_bits[j] == 1:
                Builder.cnf.append([c])
            else:
                Builder.cnf.append([-c])

            var_b.append(c)

        product = Builder.gf16_mul(var_a[i], var_b, f"matrix_{i}")
        result.append(product)
    return result



