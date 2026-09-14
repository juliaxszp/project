from src.gift_cofb_analysis import recover_key_gift_cofb

TRUE_KEY = bytes.fromhex(
    "000102030405060708090A0B0C0D0E0F"
)

NONCE = bytes.fromhex(
    "000102030405060708090A0B0C0D0E0F"
)

ASSOCIATED_DATA = b""

MESSAGE = b""

KNOWN_CIPHERTEXT = b""

KNOWN_TAG = bytes.fromhex(
    "368965836D36614DE2FC24D0F801B9AF"
)

def test_recover_one_unknown_key_bit():
    result = recover_key_gift_cofb(
        true_key=TRUE_KEY,
        unknown_positions=[127],
        nonce=NONCE,
        associated_data=ASSOCIATED_DATA,
        message=MESSAGE,
        known_ciphertext=KNOWN_CIPHERTEXT,
        known_tag=KNOWN_TAG
    )

    assert (
        result["recovered_key"]
        is not None
    )

    assert (
        result["recovered_key"]
        == TRUE_KEY
    )

    assert result["unique"]

    print(
        "\nRecovered key:",
        result[
            "recovered_key"
        ].hex().upper()
    )

    print(
        "Build time:",
        f'{result["build_time"]:.6f} s'
    )

    print(
        "Solve time:",
        f'{result["solve_time"]:.6f} s'
    )

    print(
        "Uniqueness check time:",
        f'{result["uniqueness_time"]:.6f} s'
    )

    print(
        "Total time:",
        f'{result["total_time"]:.6f} s'
    )

    print(
        "Unique key:",
        result["unique"]
    )

    print(
        "SAT variables:",
        result["variables"]
    )

    print(
        "CNF clauses:",
        result["clauses"]
    )

def test_key_recovery_increasing_unknown_bits():
    unknown_counts = [
        1,
        2,
        4,
        8
    ]

    print()

    print(
        "UNKNOWN | KNOWN | BUILD | "
        "SOLVE | UNIQUE CHECK | TOTAL | "
        "CORRECT"
    )

    print(
        "------------------------------------------------"
        "---------------------------"
    )

    for unknown_count in unknown_counts:
        unknown_positions = list(
            range(
                128 - unknown_count,
                128
            )
        )

        result = recover_key_gift_cofb(
            true_key=TRUE_KEY,
            unknown_positions=(
                unknown_positions
            ),
            nonce=NONCE,
            associated_data=(
                ASSOCIATED_DATA
            ),
            message=MESSAGE,
            known_ciphertext=(
                KNOWN_CIPHERTEXT
            ),
            known_tag=KNOWN_TAG
        )

        recovered_key = result[
            "recovered_key"
        ]

        correct = (
            recovered_key
            == TRUE_KEY
        )

        print(
            f"{unknown_count:7} | "
            f"{128 - unknown_count:5} | "
            f"{result['build_time']:5.2f}s | "
            f"{result['solve_time']:5.2f}s | "
            f"{result['uniqueness_time']:11.2f}s | "
            f"{result['total_time']:5.2f}s | "
            f"{correct}"
        )

        assert recovered_key is not None
        assert correct
        assert result["unique"]

def test_recover_16_unknown_key_bits():
    unknown_count = 16

    unknown_positions = list(
        range(
            128 - unknown_count,
            128
        )
    )

    result = recover_key_gift_cofb(
        true_key=TRUE_KEY,
        unknown_positions=unknown_positions,
        nonce=NONCE,
        associated_data=ASSOCIATED_DATA,
        message=MESSAGE,
        known_ciphertext=KNOWN_CIPHERTEXT,
        known_tag=KNOWN_TAG
    )

    recovered_key = result[
        "recovered_key"
    ]

    correct = (
        recovered_key == TRUE_KEY
    )

    print()

    print(
        "Unknown bits:",
        unknown_count
    )

    print(
        "Known bits:",
        128 - unknown_count
    )

    if recovered_key is not None:
        print(
            "Recovered key:",
            recovered_key.hex().upper()
        )
    else:
        print(
            "Recovered key: NONE"
        )

    print(
        "Correct key:",
        correct
    )

    print(
        "Unique key:",
        result["unique"]
    )

    print(
        "Build time:",
        f'{result["build_time"]:.3f} s'
    )

    print(
        "Solve time:",
        f'{result["solve_time"]:.3f} s'
    )

    print(
        "Uniqueness check time:",
        f'{result["uniqueness_time"]:.3f} s'
    )

    print(
        "Total time:",
        f'{result["total_time"]:.3f} s'
    )

    print(
        "SAT variables:",
        result["variables"]
    )

    print(
        "CNF clauses:",
        result["clauses"]
    )

    assert recovered_key is not None