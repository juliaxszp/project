def create_key(Builder, prefix="key"):
    key = []

    for bit in range(128):
        var = Builder.var(f"{prefix}_{bit}")
        key.append(var)

    return key