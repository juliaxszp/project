from src.ASCON.initialization import initialization
from src.ASCON.associated_data import associated_data_phase
from src.ASCON.plaintext import process_plaintext
from src.ASCON.finalization import finalization, extract_tag


def encrypt(Builder, key, nonce, associated_data, plaintext):
    # Initialization
    state = initialization(
        Builder,
        key,
        nonce
    )

    # Associated Data
    state = associated_data_phase(
        Builder,
        state,
        associated_data
    )

    # Plaintext
    state, ciphertext = process_plaintext(
        Builder,
        state,
        plaintext
    )

    # Finalization
    state = finalization(
        Builder,
        state,
        key
    )

    # Tag
    tag = extract_tag(state)

    return ciphertext, tag