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

def cofb_initialize(builder, nonce, key, prefix="cofb_initialize"):
    if len(nonce) != 128:
        raise ValueError(
            "COFB nonce must contain 128 bits"
        )

    if len(key) != 128:
        raise ValueError(
            "COFB key must contain 128 bits"
        )

    y0 = cofb_gift_encrypt(
        builder,
        nonce,
        key,
        f"{prefix}_gift"
    )

    l = list(y0[:64])

    return y0, l

def cofb_mask_block(builder, l, prefix="cofb_mask_block"):
    if len(l) != 64:
        raise ValueError(
            "COFB mask L must contain 64 bits"
        )

    output = list(l)

    for i in range(64):
        zero_var = builder.var(
            f"{prefix}_zero_{i}"
        )

        builder.cnf.append(
            [-zero_var]
        )

        output.append(
            zero_var
        )

    return output

def cofb_xor_blocks(builder, blocks, prefix="cofb_xor_blocks"):
    if len(blocks) == 0:
        raise ValueError(
            "At least one block is required"
        )

    block_length = len(
        blocks[0]
    )

    for block in blocks:
        if len(block) != block_length:
            raise ValueError(
                "All blocks must have the same length"
            )

    output = []

    for i in range(block_length):
        output_var = builder.var(
            f"{prefix}_{i}"
        )

        xor_vars = []

        for block in blocks:
            xor_vars.append(
                block[i]
            )

        xor_vars.append(
            output_var
        )

        builder.xor(
            xor_vars
        )

        output.append(
            output_var
        )

    return output

def cofb_triple_squared(builder, l, prefix="cofb_triple_squared"):
    first_triple = cofb_triple(
        builder,
        l,
        f"{prefix}_first"
    )

    second_triple = cofb_triple(
        builder,
        first_triple,
        f"{prefix}_second"
    )

    return second_triple

def cofb_process_associated_data(builder, associated_data, y, l, key, message_is_empty, prefix="cofb_ad"):
    ad_blocks = cofb_pad(
        builder,
        associated_data,
        block_size=128,
        prefix=f"{prefix}_pad"
    )

    for block_index in range(
        len(ad_blocks) - 1
    ):
        l = cofb_double(
            builder,
            l,
            f"{prefix}_double_{block_index}"
        )

        g_y = cofb_g(
            builder,
            y,
            f"{prefix}_g_{block_index}"
        )

        mask = cofb_mask_block(
            builder,
            l,
            f"{prefix}_mask_{block_index}"
        )

        x = cofb_xor_blocks(
            builder,
            [
                ad_blocks[block_index],
                g_y,
                mask
            ],
            f"{prefix}_x_{block_index}"
        )

        y = cofb_gift_encrypt(
            builder,
            x,
            key,
            f"{prefix}_gift_{block_index}"
        )

    last_block_index = len(
        ad_blocks
    ) - 1

    if (
        len(associated_data) != 0
        and
        len(associated_data) % 128 == 0
    ):
        l = cofb_triple(
            builder,
            l,
            f"{prefix}_last_triple"
        )
    else:
        l = cofb_triple_squared(
            builder,
            l,
            f"{prefix}_last_triple_squared"
        )

    if message_is_empty:
        l = cofb_triple_squared(
            builder,
            l,
            f"{prefix}_empty_message"
        )

    g_y = cofb_g(
        builder,
        y,
        f"{prefix}_g_last"
    )

    mask = cofb_mask_block(
        builder,
        l,
        f"{prefix}_mask_last"
    )

    x = cofb_xor_blocks(
        builder,
        [
            ad_blocks[last_block_index],
            g_y,
            mask
        ],
        f"{prefix}_x_last"
    )

    y = cofb_gift_encrypt(
        builder,
        x,
        key,
        f"{prefix}_gift_last"
    )

    return y, l