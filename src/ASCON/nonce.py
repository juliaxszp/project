def create_nonce(Builder, prefix="nonce"):
    nonce = []

    for bit in range(128):
        var = Builder.var(f"{prefix}_{bit}")
        nonce.append(var)

    return nonce