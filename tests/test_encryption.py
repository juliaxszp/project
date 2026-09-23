from src.ascon import BasicFunctions
from src.ASCON.encryption import encrypt
from src.ASCON.key import create_key
from src.ASCON.nonce import create_nonce
from src.ASCON.associated_data import create_associated_data
from src.ASCON.plaintext import create_plaintext


def test_encrypt_structure():
    builder = BasicFunctions()

    key = create_key(builder)
    nonce = create_nonce(builder)

    associated_data = create_associated_data(
        builder,
        64
    )

    plaintext = create_plaintext(
        builder,
        64
    )

    ciphertext, tag = encrypt(
        builder,
        key,
        nonce,
        associated_data,
        plaintext
    )

    assert len(ciphertext) == 64
    assert len(tag) == 128