from basics import *
from Rotate_Right_UNIVERSAL import *

def Linear_Diffusion_S(Builder, S, a, b):
    output = []

    ROR_a = rotate_right(S, a)
    ROR_b = rotate_right(S, b)

    for i in range(64):
        out = Builder.var(f"Linear_Diffusion_{i}")
        Builder.xor([out, S[i],ROR_a[i], ROR_b[i]])
        output.append(out)

    return output