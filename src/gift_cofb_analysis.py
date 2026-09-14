from time import perf_counter
from pysat.solvers import Kissat404
from .basics import BasicFunctions
from .gift_cofb import gift_cofb_encrypt

def bytes_to_fixed_sat_bits(
    builder,
    data,
    prefix
):
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

def key_to_sat_bits_with_unknowns(
    builder,
    true_key,
    unknown_positions,
    prefix="recovery_key"
):
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

    for byte in true_key:
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

def constrain_sat_bits_to_bytes(
    builder,
    bits,
    expected
):
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

def sat_bits_to_bytes(
    bits,
    model
):
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

def recover_key_gift_cofb(
    true_key,
    unknown_positions,
    nonce,
    associated_data,
    message,
    known_ciphertext,
    known_tag
):
    total_start = perf_counter()
    build_start = perf_counter()

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

    build_time = (
        perf_counter()
        -
        build_start
    )

    number_of_variables = (
        builder.idp.top
    )

    number_of_clauses = len(
        builder.cnf.clauses
    )

    solve_start = perf_counter()

    with Kissat404(
        bootstrap_with=builder.cnf.clauses
    ) as solver:

        satisfiable = solver.solve()

        solve_time = (
            perf_counter()
            -
            solve_start
        )

        if not satisfiable:
            total_time = (
                perf_counter()
                -
                total_start
            )

            return {
                "recovered_key": None,
                "build_time": build_time,
                "solve_time": solve_time,
                "uniqueness_time": 0.0,
                "total_time": total_time,
                "unique": False,
                "variables": number_of_variables,
                "clauses": number_of_clauses
            }

        model = solver.get_model()

    model_set = set(model)

    recovered_key = sat_bits_to_bytes(
        key_bits,
        model
    )

    blocking_clause = []

    for var in key_bits:
        if var in model_set:
            blocking_clause.append(
                -var
            )
        else:
            blocking_clause.append(
                var
            )

    second_clauses = (
        builder.cnf.clauses
        +
        [blocking_clause]
    )

    uniqueness_start = perf_counter()

    with Kissat404(
        bootstrap_with=second_clauses
    ) as second_solver:

        second_solution = (
            second_solver.solve()
        )

    uniqueness_time = (
        perf_counter()
        -
        uniqueness_start
    )

    unique = not second_solution

    total_time = (
        perf_counter()
        -
        total_start
    )

    return {
        "recovered_key": recovered_key,
        "build_time": build_time,
        "solve_time": solve_time,
        "uniqueness_time": uniqueness_time,
        "total_time": total_time,
        "unique": unique,
        "variables": number_of_variables,
        "clauses": number_of_clauses
    }