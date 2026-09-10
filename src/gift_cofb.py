from .gift import gift128

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

def cofb_g(builder, y, prefix="cofb_g"):
    if len(y) != 128:
        raise ValueError("COFB G expects 128 bits")

    y1 = y[:64]
    y2 = y[64:]

    rotated_y1 = y1[1:] + y1[:1]

    source_bits = y2 + rotated_y1

    output = []

    for i in range(128):
        output_var = builder.var(
            f"{prefix}_{i}"
        )

        builder.equals(
            output_var,
            source_bits[i]
        )

        output.append(output_var)

    return output

def cofb_double(builder, l, prefix="cofb_double"):
    if len(l) != 64:
        raise ValueError("COFB double expects 64 bits")

    carry = l[0]

    zero_var = builder.var(
        f"{prefix}_zero"
    )

    builder.cnf.append([-zero_var])

    shifted = l[1:] + [zero_var]

    output = []

    reduction_positions = {
        59,
        60,
        62,
        63
    }

    for i in range(64):
        output_var = builder.var(
            f"{prefix}_{i}"
        )

        if i in reduction_positions:
            builder.xor([
                shifted[i],
                carry,
                output_var
            ])
        else:
            builder.equals(
                output_var,
                shifted[i]
            )

        output.append(output_var)

    return output

def cofb_triple(builder, l, prefix="cofb_triple"):
    doubled = cofb_double(
        builder,
        l,
        f"{prefix}_double"
    )

    output = []

    for i in range(64):
        output_var = builder.var(
            f"{prefix}_{i}"
        )

        builder.xor([
            l[i],
            doubled[i],
            output_var
        ])

        output.append(output_var)

    return output

def cofb_block_to_gift_state(block):
    if len(block) != 128:
        raise ValueError(
            "GIFT block must contain 128 bits"
        )

    state = []

    for row in range(4):
        start = row * 32
        end = start + 32

        state_row = block[start:end]

        state.append(
            list(reversed(state_row))
        )

    return state

def cofb_key_to_gift_key_state(key):
    if len(key) != 128:
        raise ValueError(
            "GIFT key must contain 128 bits"
        )

    key_state = []

    for word in range(8):
        start = word * 16
        end = start + 16

        key_word = key[start:end]

        key_state.append(
            list(reversed(key_word))
        )

    return key_state

def gift_state_to_cofb_block(state):
    if len(state) != 4:
        raise ValueError(
            "GIFT state must contain 4 rows"
        )

    block = []

    for row in range(4):
        if len(state[row]) != 32:
            raise ValueError(
                "Each GIFT state row must contain 32 bits"
            )

        block.extend(
            reversed(state[row])
        )

    return block

def cofb_gift_encrypt(builder, block, key, prefix="cofb_gift_encrypt"):
    state = cofb_block_to_gift_state(
        block
    )

    key_state = cofb_key_to_gift_key_state(
        key
    )

    output_state = gift128(
        builder,
        state,
        key_state,
        prefix
    )

    output_block = gift_state_to_cofb_block(
        output_state
    )

    return output_block