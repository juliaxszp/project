import csv
import os
import random
import re
import time

from pysat.solvers import Kissat404

from src.basics import BasicFunctions
from src.ASCON.key import create_key
from src.ASCON.nonce import create_nonce
from src.ASCON.associated_data import create_associated_data
from src.ASCON.plaintext import create_plaintext
from src.ASCON.encryption import encrypt
from src.ASCON.sat_utils import force_bit, extract_bits
from src.ASCON.utils import int_to_bits

CSV_FILENAME = "wyniki_ascon_kat_30.csv"
KAT_FILEPATH = "LWC_AEAD_KAT_128_128.txt"


def load_all_official_kat_vectors(filepath=KAT_FILEPATH):
    """Wczytuje WSZYSTKIE oficjalne wektory KAT NIST bezpośrednio z pliku .txt."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Nie znaleziono pliku {filepath}! Pobierz go najpierw komendą:\n"
            f"curl -O https://raw.githubusercontent.com/ascon/ascon-c/main/tests/LWC_AEAD_KAT_128_128.txt"
        )

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.split("Count = ")
    kat_vectors = []

    for block in blocks[1:]:
        lines = block.strip().splitlines()
        data = {}

        count_match = re.search(r"^(\d+)", lines[0])
        if not count_match:
            continue

        count_val = int(count_match.group(1))

        for line in lines:
            if "Key = " in line:
                data["key"] = int(line.split(" = ")[1], 16)
            elif "Nonce = " in line:
                data["nonce"] = int(line.split(" = ")[1], 16)
            elif "PT = " in line:
                pt_hex = line.split(" = ")[1]
                data["pt"] = int(pt_hex[:16], 16) if pt_hex else 0

        if "key" in data and "nonce" in data:
            kat_vectors.append(
                {
                    "kat_id": f"KAT_NIST_{count_val:04d}",
                    "key": data["key"],
                    "nonce": data["nonce"],
                    "pt": data.get("pt", 0),
                }
            )

    return kat_vectors


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


def run_single_experiment(kat_entry, unknown_count, pattern, seed=None):
    """Przeprowadza eksperyment SAT dla konkretnego wektora KAT NIST."""
    target_key = int_to_bits(kat_entry["key"], 128)
    target_nonce = int_to_bits(kat_entry["nonce"], 128)
    target_pt = int_to_bits(kat_entry["pt"], 64)

    # 1. Generowanie wartości CT i Tag dla konkretnego wpisu KAT
    builder_gen = BasicFunctions()
    key_gen = create_key(builder_gen)
    nonce_gen = create_nonce(builder_gen)
    ad_gen = create_associated_data(builder_gen, 0)
    pt_gen = create_plaintext(builder_gen, 64)

    ct_gen, tag_gen = encrypt(builder_gen, key_gen, nonce_gen, ad_gen, pt_gen)

    for i in range(128):
        force_bit(builder_gen, key_gen[i], target_key[i])
        force_bit(builder_gen, nonce_gen[i], target_nonce[i])

    for i, var in enumerate(pt_gen):
        force_bit(builder_gen, var, target_pt[i])

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

    # Wymuszenie znanych wygenerowanych wartości (PT, CT, Tag, Nonce)
    for i, var in enumerate(pt_att):
        force_bit(builder_att, var, target_pt[i])
    for i, bit in enumerate(known_ct):
        force_bit(builder_att, ct_att[i], bit)
    for i, bit in enumerate(known_tag):
        force_bit(builder_att, tag_att[i], bit)
    for i in range(128):
        force_bit(builder_att, nonce_att[i], target_nonce[i])

    # Wyznaczanie indeksów bitów klucza do ukrycia
    unknown_indices = get_unknown_indices(unknown_count, pattern, 128, seed)
    unknown_set = set(unknown_indices)

    # Zamrażanie pozostałych (znanych) bitów klucza
    for i in range(128):
        if i not in unknown_set:
            force_bit(builder_att, key_att[i], target_key[i])

    # 3. Uruchomienie ataku SAT za pomocą Kissat404
    solver_att = Kissat404(builder_att.cnf)

    start_time = time.time()
    is_sat = solver_att.solve()
    elapsed_time = time.time() - start_time

    assert (
        is_sat
    ), f"Kissat404 powinien znaleźć rozwiązanie dla {kat_entry['kat_id']}!"

    model_att = solver_att.get_model()
    recovered_key = extract_bits(model_att, key_att)
    is_correct = recovered_key == target_key
    solver_att.delete()

    return elapsed_time, is_correct, unknown_indices


def append_to_csv(filename, row):
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(
                [
                    "ID_KAT",
                    "Bity_Liczba",
                    "Wzorzec",
                    "Czas_s",
                    "Status",
                    "Ukryte_Indeksy",
                    "Solver",
                ]
            )
        writer.writerow(row)


def run_full_kat_benchmark():
    all_kats = load_all_official_kat_vectors()
    print(f"Pomyślnie załadowano {len(all_kats)} oficjalnych wektorów KAT NIST!")

    # Zagęszczony zakres bitów z dużą próbką statystyczną
    bit_counts = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    patterns = ["first", "last", "every_2nd", "every_4th", "random"]
    iterations_per_pattern = 5  # Liczba prób dla każdego zestawu

    print("=" * 85)
    print("   BENCHMARK SAT (FULL NIST KAT DATASET) - KISSAT 4.0.4")
    print("=" * 85)
    print(
        f"{'ID KAT':<14} | {'Bity':<5} | {'Wzorzec':<10} | {'Czas [s]':<12} | Status"
    )
    print("-" * 85)

    for count in bit_counts:
        for pattern in patterns:
            for _ in range(iterations_per_pattern):
                # Losujemy 1 ze wszystkich 1023 wektorów NIST
                selected_kat = random.choice(all_kats)
                seed_val = random.randint(1, 100000)

                t, ok, indices = run_single_experiment(
                    selected_kat, count, pattern, seed=seed_val
                )

                status = "OK" if ok else "BŁĄD"
                indices_str = ";".join(map(str, indices))

                print(
                    f"{selected_kat['kat_id']:<14} | {count:<5} | {pattern:<10} | {t:<12.4f} | {status}"
                )

                append_to_csv(
                    CSV_FILENAME,
                    [
                        selected_kat["kat_id"],
                        count,
                        pattern,
                        f"{t:.4f}",
                        status,
                        indices_str,
                        "Kissat404",
                    ],
                )
        print("-" * 85)


if __name__ == "__main__":
    run_full_kat_benchmark()