import csv
import os
import random
import time

# Import Twojego dedykowanego modułu Kissat404 z projektu
from pysat.solvers import Kissat404

from src.basics import BasicFunctions
from src.ASCON.key import create_key
from src.ASCON.nonce import create_nonce
from src.ASCON.associated_data import create_associated_data
from src.ASCON.plaintext import create_plaintext
from src.ASCON.encryption import encrypt
from src.ASCON.sat_utils import force_bit, extract_bits
from src.ASCON.utils import int_to_bits

# Oficjalne wektory KAT NIST Ascon-128 v1.2
OFFICIAL_KEY_HEX = 0x000102030405060708090A0B0C0D0E0F
OFFICIAL_NONCE_HEX = 0x000102030405060708090A0B0C0D0E0F

TARGET_KEY = int_to_bits(OFFICIAL_KEY_HEX, 128)
TARGET_NONCE = int_to_bits(OFFICIAL_NONCE_HEX, 128)

CSV_FILENAME = "wyniki_ascon_sat_kissat.csv"


def get_unknown_indices(count, pattern, total_length=128, seed=None):
    """Generuje indeksy bitów do ukrycia na podstawie wybranego wzorca."""
    if pattern == "first":
        return list(range(count))
    elif pattern == "last":
        return list(range(total_length - count, total_length))
    elif pattern == "every_2nd":
        return [i * 2 for i in range(count)]
    elif pattern == "every_4th":
        return [i * 4 for i in range(count)]
    elif pattern == "random":
        if seed is not None:
            random.seed(seed)
        return sorted(random.sample(range(total_length), count))
    else:
        raise ValueError(f"Nieznany wzorzec: {pattern}")


def run_single_experiment(unknown_count, pattern, seed=None):
    """Przeprowadza eksperyment SAT odzyskiwania klucza przy użyciu Kissat404."""
    # 1. Generowanie wzorcowego CT i Tagu (KAT NIST)
    builder_gen = BasicFunctions()
    key_gen = create_key(builder_gen)
    nonce_gen = create_nonce(builder_gen)
    ad_gen = create_associated_data(builder_gen, 0)
    pt_gen = create_plaintext(builder_gen, 64)

    ct_gen, tag_gen = encrypt(builder_gen, key_gen, nonce_gen, ad_gen, pt_gen)

    for i in range(128):
        force_bit(builder_gen, key_gen[i], TARGET_KEY[i])
        force_bit(builder_gen, nonce_gen[i], TARGET_NONCE[i])

    for var in pt_gen:
        force_bit(builder_gen, var, 0)

    # Używamy kissat404 do wygenerowania znanego stanu
    solver_gen = Kissat404(builder_gen.cnf)
    solver_gen.solve()
    model_gen = solver_gen.get_model()

    known_ct = extract_bits(model_gen, ct_gen)
    known_tag = extract_bits(model_gen, tag_gen)
    solver_gen.delete()

    # 2. Tworzenie właściwego modelu ataku SAT
    builder_att = BasicFunctions()
    key_att = create_key(builder_att)
    nonce_att = create_nonce(builder_att)
    ad_att = create_associated_data(builder_att, 0)
    pt_att = create_plaintext(builder_att, 64)

    ct_att, tag_att = encrypt(builder_att, key_att, nonce_att, ad_att, pt_att)

    # Wszystkie znane wartości (PT, CT, Tag, Nonce)
    for var in pt_att:
        force_bit(builder_att, var, 0)
    for i, bit in enumerate(known_ct):
        force_bit(builder_att, ct_att[i], bit)
    for i, bit in enumerate(known_tag):
        force_bit(builder_att, tag_att[i], bit)
    for i in range(128):
        force_bit(builder_att, nonce_att[i], TARGET_NONCE[i])

    # Wyznaczamy nieznane indeksy klucza
    unknown_indices = set(
        get_unknown_indices(unknown_count, pattern, 128, seed)
    )

    # Zamrażamy znane bity klucza
    for i in range(128):
        if i not in unknown_indices:
            force_bit(builder_att, key_att[i], TARGET_KEY[i])

    # 3. Pomiar czasu rozwiązywania problemu przez Kissat404
    solver_att = Kissat404(builder_att.cnf)

    start_time = time.time()
    is_sat = solver_att.solve()
    elapsed_time = time.time() - start_time

    assert is_sat, "Kissat404 powinien znaleźć rozwiązanie dla prawidłowych danych!"

    model_att = solver_att.get_model()
    recovered_key = extract_bits(model_att, key_att)
    is_correct = recovered_key == TARGET_KEY
    solver_att.delete()

    return elapsed_time, is_correct


def append_to_csv(filename, row):
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Bity", "Wzorzec", "Czas_s", "Status", "Solver"])
        writer.writerow(row)


def run_detailed_benchmark():
    bit_counts = [4, 8, 12, 16, 17, 18, 19, 20, 21]
    patterns = ["first", "last", "every_2nd", "every_4th", "random"]
    random_runs = 3

    print("=" * 75)
    print("   BENCHMARK SAT KEY RECOVERY - ASCON-128 v1.2 (KISSAT 4.0.4)")
    print("=" * 75)
    print(f"{'Bity':<6} | {'Wzorzec':<10} | {'Czas [s]':<12} | Status")
    print("-" * 75)

    for count in bit_counts:
        for pattern in patterns:
            if pattern == "random":
                times = []
                all_ok = True

                for r in range(random_runs):
                    t, ok = run_single_experiment(
                        count, pattern, seed=42 + r
                    )
                    times.append(t)
                    if not ok:
                        all_ok = False

                avg_time = sum(times) / len(times)
                status = "OK" if all_ok else "BŁĄD"
                print(
                    f"{count:<6} | {pattern:<10} | {avg_time:<12.4f} | {status} (Kissat404 śr. z {random_runs})"
                )
                append_to_csv(
                    CSV_FILENAME,
                    [count, pattern, f"{avg_time:.4f}", status, "Kissat404"],
                )
            else:
                t, ok = run_single_experiment(count, pattern)
                status = "OK" if ok else "BŁĄD"
                print(f"{count:<6} | {pattern:<10} | {t:<12.4f} | {status} (Kissat404)")
                append_to_csv(
                    CSV_FILENAME, [count, pattern, f"{t:.4f}", status, "Kissat404"]
                )
        print("-" * 75)


if __name__ == "__main__":
    run_detailed_benchmark()