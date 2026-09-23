from pysat.solvers import Solver

from src.ascon import BasicFunctions
from src.ASCON.encryption import encrypt
from src.ASCON.key import create_key
from src.ASCON.nonce import create_nonce
from src.ASCON.associated_data import create_associated_data
from src.ASCON.plaintext import create_plaintext
from src.ASCON.sat_utils import force_bit, extract_bits


def test_recover_8_unknown_key_bits():
    # === KROK 1: Generowanie spójnego szyfrogramu z modelu ===
    builder_gen = BasicFunctions()

    key_gen = create_key(builder_gen)
    nonce_gen = create_nonce(builder_gen)
    ad_gen = create_associated_data(builder_gen, 0)
    pt_gen = create_plaintext(builder_gen, 64)

    ct_gen, tag_gen = encrypt(
        builder_gen,
        key_gen,
        nonce_gen,
        ad_gen,
        pt_gen
    )

    # Definiujemy pełny 128-bitowy klucz testowy
    target_key_value = [
        0, 1, 0, 1, 1, 0, 1, 1,
        1, 0, 0, 1, 0, 1, 1, 0,
        0, 1, 1, 0, 1, 0, 0, 1,
        1, 1, 0, 0, 1, 0, 1, 0,
        0, 0, 1, 1, 0, 1, 0, 1,
        1, 1, 1, 0, 0, 1, 0, 0,
        1, 0, 1, 1, 1, 0, 0, 1,
        0, 1, 0, 0, 1, 1, 1, 0,
        1, 1, 0, 1, 0, 0, 1, 0,
        0, 1, 1, 1, 1, 0, 1, 1,
        1, 0, 0, 0, 1, 1, 0, 1,
        0, 1, 0, 1, 1, 1, 0, 0,
        1, 0, 1, 0, 0, 1, 1, 1,
        0, 0, 1, 1, 1, 0, 1, 0,
        1, 1, 0, 0, 0, 1, 0, 1,
        0, 1, 1, 0, 1, 1, 0, 0,
    ]

    # Ustawiamy pełny klucz, nonce i plaintext dla generacji
    for i in range(128):
        force_bit(builder_gen, key_gen[i], target_key_value[i])

    for var in nonce_gen:
        force_bit(builder_gen, var, 0)

    for var in pt_gen:
        force_bit(builder_gen, var, 0)

    # Rozwiązujemy SAT, żeby poznać spójne wyjście (Ciphertext i Tag)
    solver_gen = Solver(name="g3")
    for clause in builder_gen.cnf:
        solver_gen.add_clause(clause)

    assert solver_gen.solve() is True, "Błąd generowania wyjścia z modelu!"
    gen_model = set(solver_gen.get_model())

    generated_ciphertext = extract_bits(gen_model, ct_gen)
    generated_tag = extract_bits(gen_model, tag_gen)
    solver_gen.delete()

    # === KROK 2: Eksperyment ataku — odzyskiwanie 8 nieznanych bitów ===
    builder_attack = BasicFunctions()

    key_at = create_key(builder_attack)
    nonce_at = create_nonce(builder_attack)
    ad_at = create_associated_data(builder_attack, 0)
    pt_at = create_plaintext(builder_attack, 64)

    ct_at, tag_at = encrypt(
        builder_attack,
        key_at,
        nonce_at,
        ad_at,
        pt_at
    )

    # Zamrażamy uzyskany Ciphertext i Tag
    for i, var in enumerate(ct_at):
        force_bit(builder_attack, var, generated_ciphertext[i])

    for i, var in enumerate(tag_at):
        force_bit(builder_attack, var, generated_tag[i])

    # Zamrażamy Nonce i Plaintext
    for var in nonce_at:
        force_bit(builder_attack, var, 0)

    for var in pt_at:
        force_bit(builder_attack, var, 0)

    # Znamy tylko pierwsze 120 bitów klucza (ostatnie 8 bitów jest NIEZNANE)
    for i in range(120):
        force_bit(builder_attack, key_at[i], target_key_value[i])

    # Solver SAT odzyskuje pozostałe 8 bitów klucza
    solver_attack = Solver(name="g3")
    for clause in builder_attack.cnf:
        solver_attack.add_clause(clause)

    assert solver_attack.solve() is True, "Solver nie znalazł rozwiązania!"
    attack_model = set(solver_attack.get_model())
    recovered_key = extract_bits(attack_model, key_at)

    # Weryfikacja czy odzyskany klucz zgadza się ze wzorcowym
    assert recovered_key == target_key_value, "Odzyskany klucz nie zgadza się z oryginalnym!"
    solver_attack.delete()