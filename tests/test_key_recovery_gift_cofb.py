from src.key_recovery_gift_cofb import recover_key_gift_cofb

def test_recover_one_unknown_key_bit():
    true_key = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
    )

    nonce = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
    )

    associated_data = b""
    message = b""

    known_ciphertext = b""

    known_tag = bytes.fromhex(
        "368965836D36614DE2FC24D0F801B9AF"
    )

    recovered_key, solve_time = (
        recover_key_gift_cofb(
            true_key=true_key,
            unknown_positions=[127],
            nonce=nonce,
            associated_data=associated_data,
            message=message,
            known_ciphertext=known_ciphertext,
            known_tag=known_tag
        )
    )

    assert recovered_key is not None

    assert recovered_key == true_key

    print(
        f"\nRecovered key: "
        f"{recovered_key.hex().upper()}"
    )

    print(
        f"Solve time: "
        f"{solve_time:.6f} s"
    )