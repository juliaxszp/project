from src.reference_gift_cofb import (
    gift128_reference,
    gift_cofb_encrypt_reference
)

def test_reference_gift128():
    key = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
    )

    plaintext = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
    )

    expected = bytes.fromhex(
        "A94AF7F9BA181DF9"
        "B2B00EB7DBFA93DF"
    )

    ciphertext = gift128_reference(
        plaintext,
        key
    )

    assert ciphertext == expected

def test_reference_gift_cofb_kat_1():
    key = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
    )

    nonce = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
    )

    associated_data = b""
    message = b""

    expected = bytes.fromhex(
        "368965836D36614DE2FC24D0F801B9AF"
    )

    ciphertext, tag = (
        gift_cofb_encrypt_reference(
            key,
            nonce,
            associated_data,
            message
        )
    )

    assert ciphertext + tag == expected

def test_reference_gift_cofb_kat_1089():
    key = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
    )

    nonce = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
    )

    message = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
        "101112131415161718191A1B1C1D1E1F"
    )

    associated_data = bytes.fromhex(
        "000102030405060708090A0B0C0D0E0F"
        "101112131415161718191A1B1C1D1E1F"
    )

    expected = bytes.fromhex(
        "BAF563C60FBEDDC5662995F4C678BE80"
        "A7F7DE9B3AD8C97AA6CA17016D2AE65"
        "08E6FB3F79B412A1627AB7DFA755E0A22"
    )

    ciphertext, tag = (
        gift_cofb_encrypt_reference(
            key,
            nonce,
            associated_data,
            message
        )
    )

    assert ciphertext + tag == expected