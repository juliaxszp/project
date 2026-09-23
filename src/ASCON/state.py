
def create_state(Builder, prefix="state"):
    state = []

    for word in range(5):
        bits = []

        for bit in range(64):
            var = Builder.var(
                f"{prefix}_S{word}_{bit}"
            )
            bits.append(var)

        state.append(bits)

    return state