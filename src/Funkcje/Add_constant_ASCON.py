def add_constant(Builder, S2, constant):
    output = []

    for i in range(64):
        out = Builder.var(f"addconst_{i}")
        constant_bit = (constant >> i) & 1

        if constant_bit == 0:
            Builder.equals(S2[i], out)
        else:
            Builder.equals_not(S2[i], out)

        output.append(out)

    return output