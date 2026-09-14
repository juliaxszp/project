from time import perf_counter
from pysat.solvers import Kissat404
from .basics import BasicFunctions
from .gift_cofb import gift_cofb_encrypt

def bytes_to_fixed_sat_bits(builder, data, prefix):
    bits = []

    for byte_index, byte in enumerate(data):
        for bit_index in range(7, -1, -1):
            var = builder.var(
                f"{prefix}_{byte_index}_{bit_index}"
            )

            bits.append(var)

            bit = (
                byte >> bit_index
            ) & 1

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

    return bits

def key_to_sat_bits_with_unknowns(builder, true_key, unknown_positions, prefix="recovery_key"):
    if len(true_key) != 16:
        raise ValueError(
            "GIFT-COFB key must contain 16 bytes"
        )

    unknown_positions = set(
        unknown_positions
    )

    for position in unknown_positions:
        if position < 0 or position >= 128:
            raise ValueError(
                "Key bit position must be "
                "between 0 and 127"
            )

    key_bits = []

    bit_position = 0

    for byte_index, byte in enumerate(true_key):
        for bit_index in range(7, -1, -1):
            var = builder.var(
                f"{prefix}_{bit_position}"
            )

            key_bits.append(var)

            if bit_position not in unknown_positions:
                bit = (
                    byte >> bit_index
                ) & 1

                if bit == 1:
                    builder.cnf.append([var])
                else:
                    builder.cnf.append([-var])

            bit_position += 1

    return key_bits

def constrain_sat_bits_to_bytes(builder, bits, expected):
    if len(bits) != len(expected) * 8:
        raise ValueError(
            "Number of SAT bits does not match "
            "expected byte length"
        )

    position = 0

    for byte in expected:
        for bit_index in range(7, -1, -1):
            bit = (
                byte >> bit_index
            ) & 1

            var = bits[position]

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

            position += 1

def sat_bits_to_bytes(bits, model):
    model_set = set(model)

    result = bytearray()

    for start in range(
        0,
        len(bits),
        8
    ):
        value = 0

        for var in bits[
            start:start + 8
        ]:
            value <<= 1

            if var in model_set:
                value |= 1

        result.append(value)

    return bytes(result)

def recover_key_gift_cofb(true_key, unknown_positions, nonce, associated_data, message, known_ciphertext, known_tag):
    builder = BasicFunctions()

    key_bits = (
        key_to_sat_bits_with_unknowns(
            builder,
            true_key,
            unknown_positions,
            "recovery_key"
        )
    )

    nonce_bits = bytes_to_fixed_sat_bits(
        builder,
        nonce,
        "recovery_nonce"
    )

    associated_data_bits = (
        bytes_to_fixed_sat_bits(
            builder,
            associated_data,
            "recovery_ad"
        )
    )

    message_bits = bytes_to_fixed_sat_bits(
        builder,
        message,
        "recovery_message"
    )

    ciphertext_bits, tag_bits = (
        gift_cofb_encrypt(
            builder,
            nonce_bits,
            associated_data_bits,
            message_bits,
            key_bits,
            "recovery_gift_cofb"
        )
    )

    constrain_sat_bits_to_bytes(
        builder,
        ciphertext_bits,
        known_ciphertext
    )

    constrain_sat_bits_to_bytes(
        builder,
        tag_bits,
        known_tag
    )

    start_time = perf_counter()

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        satisfiable = solver.solve()

        solve_time = (perf_counter() -start_time)

        if not satisfiable:
            return None, solve_time

        model = solver.get_model()

    recovered_key = sat_bits_to_bytes(
        key_bits,
        model
    )

    return recovered_key, solve_time