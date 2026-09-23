from .basics import *
from src.ASCON.constants import get_const_zero, get_const_one



def add_constant(Builder, S2, constant, prefix=""):
    output = []

    for i in range(64):
        out = Builder.var(f"{prefix}addconst_{i}")
        constant_bit = (constant >> i) & 1

        if constant_bit == 0:
            Builder.equals(S2[i], out)
        else:
            Builder.equals_not(S2[i], out)

        output.append(out)

    return output




def S_box(Builder, S0, S1, S2, S3, S4, prefix=""):
    output = []

    X0 = Builder.var(f"{prefix}S0_xor_S4")
    Builder.xor([X0, S0, S4])

    X1 = Builder.var(f"{prefix}S4_xor_S3")
    Builder.xor([X1, S4, S3])
    
    X2 = Builder.var(f"{prefix}S2_xor_S1")
    Builder.xor([X2, S2, S1])

    N0 = Builder.var(f"{prefix}N0_equals_not_X0")
    Builder.equals_not(N0, X0)

    N1 = Builder.var(f"{prefix}N1_equals_not_S1")
    Builder.equals_not(N1, S1)

    N2 = Builder.var(f"{prefix}N2_equals_not_X2")
    Builder.equals_not(N2, X2)

    N3 = Builder.var(f"{prefix}N3_equals_not_S3")
    Builder.equals_not(N3, S3)

    N4 = Builder.var(f"{prefix}N4_equals_not_X1")
    Builder.equals_not(N4, X1)

    U0 = Builder.var(f"{prefix}N0_and_S1")
    Builder.equal_and(U0, [N0, S1])

    U1 = Builder.var(f"{prefix}N1_and_X2")
    Builder.equal_and(U1, [N1, X2])

    U2 = Builder.var(f"{prefix}N2_and_S3")
    Builder.equal_and(U2, [N2, S3])

    U3 = Builder.var(f"{prefix}N3_and_X1")
    Builder.equal_and(U3, [N3, X1])

    U4 = Builder.var(f"{prefix}N4_and_X0")
    Builder.equal_and(U4, [N4, X0])

    Y0 = Builder.var(f"{prefix}X0_xor_U1")
    Builder.xor([Y0, X0, U1])

    Y1 = Builder.var(f"{prefix}S1_xor_U2")
    Builder.xor([Y1, S1, U2])

    Y2 = Builder.var(f"{prefix}X2_xor_U3")
    Builder.xor([Y2, X2, U3])

    Y3 = Builder.var(f"{prefix}S3_xor_U4")
    Builder.xor([Y3, S3, U4])

    Y4 = Builder.var(f"{prefix}X1_xor_U0")
    Builder.xor([Y4, X1, U0])

    Z0 = Builder.var(f"{prefix}Y0_xor_Y4")
    Builder.xor([Z0, Y0, Y4])
    
    Z1 = Builder.var(f"{prefix}Y1_xor_Y0")
    Builder.xor([Z1, Y1, Y0])
    
    Z2 = Builder.var(f"{prefix}Z2_equals_not_Y2")
    Builder.equals_not(Z2, Y2)
    
    Z3 = Builder.var(f"{prefix}Y3_xor_Y2")
    Builder.xor([Z3, Y3, Y2])

    Z4 = Builder.var(f"{prefix}Z4_equals_Y4")
    Builder.equals(Z4, Y4)

    output.append(Z0)
    output.append(Z1)
    output.append(Z2)
    output.append(Z3)
    output.append(Z4)

    return output 


def S_box_64(Builder, S0, S1, S2, S3, S4, prefix=""):
    S0_output = []
    S1_output = []
    S2_output = []
    S3_output = []
    S4_output = []
    for i in range(64):
        wynik = S_box(Builder, S0[i], S1[i], S2[i], S3[i], S4[i], prefix=f"{prefix}Sbox_{i}_")
        S0_output.append(wynik[0])
        S1_output.append(wynik[1])
        S2_output.append(wynik[2])
        S3_output.append(wynik[3])
        S4_output.append(wynik[4])

    return S0_output, S1_output, S2_output, S3_output, S4_output



def rotate_right(S, n):
    liczba_bitow = len(S)

    output = []

    for i in range(liczba_bitow):
        output.append(S[(i + n) % liczba_bitow])

    return output




def Linear_Diffusion(Builder, S, a, b, prefix=""):
    output = []

    ROR_a = rotate_right(S, a)
    ROR_b = rotate_right(S, b)

    for i in range(64):
        out = Builder.var(f"{prefix}Linear_Diffusion_{i}")
        Builder.xor([out, S[i], ROR_a[i], ROR_b[i]])
        output.append(out)

    return output