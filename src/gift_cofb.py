def cofb_pad(builder, data_vars, block_size=128, prefix="cofb_pad"):
    padded = list(data_vars)

    if len(data_vars) == 0 or len(data_vars) % block_size != 0:
        one_var = builder.var(f"{prefix}_one")

        builder.cnf.append([one_var])
        padded.append(one_var)

        zeros_needed = (
            block_size - (len(padded) % block_size)
        ) % block_size

        for i in range(zeros_needed):
            zero_var = builder.var(f"{prefix}_zero_{i}")

            builder.cnf.append([-zero_var])
            padded.append(zero_var)

    blocks = []

    for start in range(
        0,
        len(padded),
        block_size
    ):
        block = padded[
            start:start + block_size
        ]

        blocks.append(block)

    return blocks