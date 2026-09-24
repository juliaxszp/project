from pysat.solvers import Kissat404
from src.full_photon import *
from tests.test_photon import hex_to_sat 
from analysis.reference_photon import photon_encrypt
import secrets
import json 
import threading
import statistics
import random
import time

def kpa265_no_ad_last():
    builder = BasicFunctions()  
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = []
    ptx = hex_to_sat(builder, "0001020304050607", "ptx")
    ciphertext_tag = "A7B9AF5BA1AA580961E102ED01CDB5FD78D1DF643CC7B703"
    split = len(ptx) // 4
    ciphertext = ciphertext_tag[:split]
    tag = ciphertext_tag[split:]
    known_ciphertext = hex_to_sat(builder, ciphertext, "cipher")
    known_tag = hex_to_sat(builder, tag, "tag")
    key = [builder.var(f"key_{i}") for i in range(128)]
    key_hex = "000102030405060708090A0B0C0D0E0F"
    key_bytes = bytes.fromhex(key_hex)
    key_bits = []
    for byte in key_bytes:
        for b in range(8):
            key_bits.append((byte >> b) & 1)
    assert len(key_bits) == 128
    known_key_bits = 120
    for i in range(known_key_bits):
        if key_bits[i] == 1:
            builder.cnf.append([key[i]])
        else:
            builder.cnf.append([-key[i]])
    print("budowanie")
    generated_ciphertext, generated_tag = photon_beetle(builder, nonce, key, A, ptx)
    print("zbudowany")
    assert len(generated_ciphertext) == len(known_ciphertext)
    assert len(generated_tag) == len(known_tag)
    for generated_bit, known_bit in zip(generated_ciphertext, known_ciphertext):
        builder.equals(generated_bit, known_bit)
    for generated_bit, known_bit in zip(generated_tag, known_tag):
        builder.equals(generated_bit, known_bit)
    print("ilosc literalow:", builder.idp.top)
    print("ilosc klauzul:", len(builder.cnf.clauses))
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    print("uruchamiany solver")
    import time
    start = time.time()
    result = solver.solve()
    lapse = time.time() - start
    print(result)
    print(f"czas {lapse} s")
    assert result
    recovered_bits = []
    model = solver.get_model()
    model_set = set(model)
    for i in range(128):
        if key[i] in model_set:
            recovered_bits.append(1)
        elif -key[i] in model_set:
            recovered_bits.append(0)

    for i in range(known_key_bits, 128):
        print(
            f"key[{i}]: "
            f"oczekiwany={key_bits[i]}, "
            f"odzyskany={recovered_bits[i]}")

        assert recovered_bits[i] == key_bits[i]

def kpa265_no_ad_first():
    builder = BasicFunctions()  
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = []
    ptx = hex_to_sat(builder, "0001020304050607", "ptx")
    ciphertext_tag = "A7B9AF5BA1AA580961E102ED01CDB5FD78D1DF643CC7B703"
    split = len(ptx) // 4
    ciphertext = ciphertext_tag[:split]
    tag = ciphertext_tag[split:]
    known_ciphertext = hex_to_sat(builder, ciphertext, "cipher")
    known_tag = hex_to_sat(builder, tag, "tag")
    key = [builder.var(f"key_{i}") for i in range(128)]
    key_hex = "000102030405060708090A0B0C0D0E0F"
    key_bytes = bytes.fromhex(key_hex)
    key_bits = []
    for byte in key_bytes:
        for b in range(8):
            key_bits.append((byte >> b) & 1)
    assert len(key_bits) == 128
    unknown_key_bits = 20
    for i in range(unknown_key_bits, 128):
        if key_bits[i] == 1:
            builder.cnf.append([key[i]])
        else:
            builder.cnf.append([-key[i]])
    print("budowanie")
    generated_ciphertext, generated_tag = photon_beetle(builder, nonce, key, A, ptx)
    print("zbudowany")
    assert len(generated_ciphertext) == len(known_ciphertext)
    assert len(generated_tag) == len(known_tag)
    for generated_bit, known_bit in zip(generated_ciphertext, known_ciphertext):
        builder.equals(generated_bit, known_bit)
    for generated_bit, known_bit in zip(generated_tag, known_tag):
        builder.equals(generated_bit, known_bit)
    print("ilosc literalow:", builder.idp.top)
    print("ilosc klauzul:", len(builder.cnf.clauses))
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    print("uruchamiany solver")
    import time
    start = time.time()
    result = solver.solve()
    lapse = time.time() - start
    print(result)
    print(f"czas {lapse} s")
    assert result
    recovered_bits = []
    model = solver.get_model()
    model_set = set(model)
    for i in range(128):
        if key[i] in model_set:
            recovered_bits.append(1)
        elif -key[i] in model_set:
            recovered_bits.append(0)
        else:
            recovered_bits.append(None)
    for i in range(unknown_key_bits):
        print(
            f"key[{i}]: "
            f"oczekiwany={key_bits[i]}, "
            f"odzyskany={recovered_bits[i]}")

        assert recovered_bits[i] == key_bits[i]


def kpa265_no_ad_random():
    builder = BasicFunctions()  
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = []
    ptx = hex_to_sat(builder, "0001020304050607", "ptx")
    ciphertext_tag = "A7B9AF5BA1AA580961E102ED01CDB5FD78D1DF643CC7B703"
    split = len(ptx) // 4
    ciphertext = ciphertext_tag[:split]
    tag = ciphertext_tag[split:]
    known_ciphertext = hex_to_sat(builder, ciphertext, "cipher")
    known_tag = hex_to_sat(builder, tag, "tag")
    key = [builder.var(f"key_{i}") for i in range(128)]
    key_hex = "000102030405060708090A0B0C0D0E0F"
    key_bytes = bytes.fromhex(key_hex)
    key_bits = []
    for byte in key_bytes:
        for b in range(8):
            key_bits.append((byte >> b) & 1)
    assert len(key_bits) == 128
    unknown_key_bits = 20
    unknown_positions = set(random.sample(range(128), unknown_key_bits))
    print("nienznane pozycje:", sorted(unknown_positions))
    for i in range(128):
        if i in unknown_positions:
            continue
        if key_bits[i] == 1:
            builder.cnf.append([key[i]])
        else:
            builder.cnf.append([-key[i]])
    print("budowanie")
    generated_ciphertext, generated_tag = photon_beetle(builder, nonce, key, A, ptx)
    print("zbudowany")
    assert len(generated_ciphertext) == len(known_ciphertext)
    assert len(generated_tag) == len(known_tag)
    for generated_bit, known_bit in zip(generated_ciphertext, known_ciphertext):
        builder.equals(generated_bit, known_bit)
    for generated_bit, known_bit in zip(generated_tag, known_tag):
        builder.equals(generated_bit, known_bit)
    print("ilosc literalow:", builder.idp.top)
    print("ilosc klauzul:", len(builder.cnf.clauses))
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    print("uruchamiany solver")
    import time
    start = time.time()
    result = solver.solve()
    lapse = time.time() - start
    print(result)
    print(f"czas {lapse} s")
    assert result
    recovered_bits = []
    model = solver.get_model()
    model_set = set(model)
    for i in range(128):
        if key[i] in model_set:
            recovered_bits.append(1)
        elif -key[i] in model_set:
            recovered_bits.append(0)
        else:
            recovered_bits.append(None)
    for i in sorted(unknown_positions):
        print(
            f"key[{i}]: "
            f"oczekiwany={key_bits[i]}, "
            f"odzyskany={recovered_bits[i]}")

        assert recovered_bits[i] == key_bits[i]

def kpa454_with_ad_last():
    builder = BasicFunctions()
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F1011121314151617", "AD")
    ptx = hex_to_sat(builder, "000102030405060708090A0B0C", "ptx")
    ciphertext_tag = "94103789DE1CFE6C7224F1E6EC2A9E64F158B76D40DA75DA5489760A03"
    split = len(ptx) // 4
    ciphertext = ciphertext_tag[:split]
    tag = ciphertext_tag[split:]
    known_ciphertext = hex_to_sat(builder, ciphertext, "cipher")
    known_tag = hex_to_sat(builder, tag, "tag")
    key = [builder.var(f"key_{i}") for i in range(128)]
    key_hex = "000102030405060708090A0B0C0D0E0F"
    key_bytes = bytes.fromhex(key_hex)
    key_bits = []
    for byte in key_bytes:
        for b  in range(8):
            key_bits.append((byte >> b) & 1)
    assert len(key_bits) == 128
    known_key_bits = 104
    for i in range(known_key_bits):
        if key_bits[i] == 1:
            builder.cnf.append([key[i]])
        else:
            builder.cnf.append([-key[i]])
    print("budowanie")
    generated_ciphertext, generated_tag = photon_beetle(builder, nonce, key, A, ptx)
    print("zbudowany")
    assert len(generated_ciphertext) == len(known_ciphertext)
    assert len(generated_tag) == len(known_tag)
    for generated_bit, known_bit in zip(generated_ciphertext, known_ciphertext):
        builder.equals(generated_bit, known_bit)
    for generated_bit, known_bit in zip(generated_tag, known_tag):
        builder.equals(generated_bit, known_bit)
    print("ilosc literalow:", builder.idp.top)
    print("ilosc klauzul:", len(builder.cnf.clauses))
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    print("uruchamiany solver")
    import time
    start = time.time()
    result = solver.solve()
    lapse = time.time() - start
    print(result)
    print(f"czas {lapse} s")
    assert result
    recovered_bits = []
    model = solver.get_model()
    model_set = set(model)
    for i in range(128):
        if key[i] in model_set:
            recovered_bits.append(1)
        elif -key[i] in model_set:
            recovered_bits.append(0)
        else:
            recovered_bits.append(None)
    for i in range(known_key_bits, 128):
        print(
            f"key[{i}]: "
            f"oczekiwany={key_bits[i]}, "
            f"odzyskany={recovered_bits[i]}")
    
        assert recovered_bits[i] == key_bits[i]

def kpa454_with_ad_first():
    builder = BasicFunctions()
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F1011121314151617", "AD")
    ptx = hex_to_sat(builder, "000102030405060708090A0B0C", "ptx")
    ciphertext_tag = "94103789DE1CFE6C7224F1E6EC2A9E64F158B76D40DA75DA5489760A03"
    split = len(ptx) // 4
    ciphertext = ciphertext_tag[:split]
    tag = ciphertext_tag[split:]
    known_ciphertext = hex_to_sat(builder, ciphertext, "cipher")
    known_tag = hex_to_sat(builder, tag, "tag")
    key = [builder.var(f"key_{i}") for i in range(128)]
    key_hex = "000102030405060708090A0B0C0D0E0F"
    key_bytes = bytes.fromhex(key_hex)
    key_bits = []
    for byte in key_bytes:
        for b  in range(8):
            key_bits.append((byte >> b) & 1)
    assert len(key_bits) == 128
    unknown_key_bits = 20
    for i in range(unknown_key_bits, 128):
        if key_bits[i] == 1:
            builder.cnf.append([key[i]])
        else:
            builder.cnf.append([-key[i]])
    print("budowanie")
    generated_ciphertext, generated_tag = photon_beetle(builder, nonce, key, A, ptx)
    print("zbudowany")
    assert len(generated_ciphertext) == len(known_ciphertext)
    assert len(generated_tag) == len(known_tag)
    for generated_bit, known_bit in zip(generated_ciphertext, known_ciphertext):
        builder.equals(generated_bit, known_bit)
    for generated_bit, known_bit in zip(generated_tag, known_tag):
        builder.equals(generated_bit, known_bit)
    print("ilosc literalow:", builder.idp.top)
    print("ilosc klauzul:", len(builder.cnf.clauses))
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    print("uruchamiany solver")
    import time
    start = time.time()
    result = solver.solve()
    lapse = time.time() - start
    print(result)
    print(f"czas {lapse} s")
    assert result
    recovered_bits = []
    model = solver.get_model()
    model_set = set(model)
    for i in range(128):
        if key[i] in model_set:
            recovered_bits.append(1)
        elif -key[i] in model_set:
            recovered_bits.append(0)
        else:
            recovered_bits.append(None)
    for i in range(unknown_key_bits):
        print(
            f"key[{i}]: "
            f"oczekiwany={key_bits[i]}, "
            f"odzyskany={recovered_bits[i]}")
    
        assert recovered_bits[i] == key_bits[i]

def kpa454_with_ad_random():
    builder = BasicFunctions()
    nonce = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F", "nonce")
    A = hex_to_sat(builder, "000102030405060708090A0B0C0D0E0F1011121314151617", "AD")
    ptx = hex_to_sat(builder, "000102030405060708090A0B0C", "ptx")
    ciphertext_tag = "94103789DE1CFE6C7224F1E6EC2A9E64F158B76D40DA75DA5489760A03"
    split = len(ptx) // 4
    ciphertext = ciphertext_tag[:split]
    tag = ciphertext_tag[split:]
    known_ciphertext = hex_to_sat(builder, ciphertext, "cipher")
    known_tag = hex_to_sat(builder, tag, "tag")
    key = [builder.var(f"key_{i}") for i in range(128)]
    key_hex = "000102030405060708090A0B0C0D0E0F"
    key_bytes = bytes.fromhex(key_hex)
    key_bits = []
    for byte in key_bytes:
        for b  in range(8):
            key_bits.append((byte >> b) & 1)
    assert len(key_bits) == 128
    unknown_key_bits = 20
    unknown_positions = set(random.sample(range(128), unknown_key_bits))
    print("nieznane pozycje:", sorted(unknown_positions))
    for i in range(128):
        if i in unknown_positions:
            continue
        if key_bits[i] == 1:
            builder.cnf.append([key[i]])
        else:
            builder.cnf.append([-key[i]])
    print("budowanie")
    generated_ciphertext, generated_tag = photon_beetle(builder, nonce, key, A, ptx)
    print("zbudowany")
    assert len(generated_ciphertext) == len(known_ciphertext)
    assert len(generated_tag) == len(known_tag)
    for generated_bit, known_bit in zip(generated_ciphertext, known_ciphertext):
        builder.equals(generated_bit, known_bit)
    for generated_bit, known_bit in zip(generated_tag, known_tag):
        builder.equals(generated_bit, known_bit)
    print("ilosc literalow:", builder.idp.top)
    print("ilosc klauzul:", len(builder.cnf.clauses))
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    print("uruchamiany solver")
    import time
    start = time.time()
    result = solver.solve()
    lapse = time.time() - start
    print(result)
    print(f"czas {lapse} s")
    assert result
    recovered_bits = []
    model = solver.get_model()
    model_set = set(model)
    for i in range(128):
        if key[i] in model_set:
            recovered_bits.append(1)
        elif -key[i] in model_set:
            recovered_bits.append(0)
        else:
            recovered_bits.append(None)
    for i in sorted(unknown_positions):
        print(
            f"key[{i}]: "
            f"oczekiwany={key_bits[i]}, "
            f"odzyskany={recovered_bits[i]}")
    
        assert recovered_bits[i] == key_bits[i]

"""if __name__ == "__main__":
    kpa454_with_ad_random()"""

#===============================
N = 100
BYTES = 16
UNKNOWN_NIBBLES_COUNT = 2

NONCE_HEX = "000102030405060708090A0B0C0D0E0F"
AD_HEX = ""


"""def generate_samples(N, BYTES):
    samples = []
    for i in range(N):
        builder = BasicFunctions()
        ptx_hex = secrets.token_hex(BYTES).upper()
        key_hex = secrets.token_hex(BYTES).upper()
        ciphertext_tag = photon_encrypt(key_hex, NONCE_HEX, AD_HEX, ptx_hex)
        sample = {
            "ptx": ptx_hex,
            "key": key_hex,
            "cipher": ciphertext_tag
        }
        samples.append(sample)
    return samples

samples = generate_samples(N, BYTES)"""
"""
print(samples[0])"""

with open("analysis/photon_samples.json", "r") as file:
    samples = json.load(file)


def get_unknown_bits(nibbles):
    unknown_bits = []

    for nibble in nibbles:
        start = nibble*4

        for bit in range(start, start + 4):
            unknown_bits.append(bit)
    return unknown_bits



def analyze_sample(sample, unknown_nibbles):
    builder = BasicFunctions()
    unknown_bits = get_unknown_bits(unknown_nibbles)
    nonce = hex_to_sat(builder, NONCE_HEX, "nonce")
    A = []
    ptx = hex_to_sat(builder, sample["ptx"], "ptx")
    split = len(sample["ptx"])
    ciphertext_hex = sample["cipher"][:split]
    tag_hex = sample["cipher"][split:]
    known_ciphertext = hex_to_sat(builder, ciphertext_hex, "cipher")
    known_tag = hex_to_sat(builder, tag_hex, "tag")
    key = [builder.var(f"key_{i}")  for i in range(128)]
    key_bytes = bytes.fromhex(sample["key"])
    key_bits = []
    for byte in key_bytes:
        for b in range(8):
            key_bits.append((byte >> b) & 1)
    for i in range(128):
        if i not in unknown_bits:
            if key_bits[i] == 1:
                builder.cnf.append([key[i]])
            else:
                builder.cnf.append([-key[i]])
    print("budowanie")
    generated_ciphertext, generated_tag = photon_beetle(builder, nonce, key, A, ptx)
    print("zbudowany")
    for generated_bit, known_bit in zip(generated_ciphertext, known_ciphertext):
            builder.equals(generated_bit, known_bit)
    for generated_bit, known_bit in zip(generated_tag, known_tag):
        builder.equals(generated_bit, known_bit)
        """
    print("ilosc literalow:", builder.idp.top)
    print("ilosc klauzul:", len(builder.cnf.clauses))
    """
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    start = time.time()
    result = solver.solve()
    lapse = time.time() - start
    if result is False:
        print(f"UNSAT po {lapse:.3f} s")
        solver.delete()
        return {
            "status": "UNSAT",
            "time": lapse
        }

    print(f"SAT, czas: {lapse:.3f} s")
    model = solver.get_model()
    model_set = set(model)
    recovered_bits = []
    for i in range(128):
        if key[i] in model_set:
            recovered_bits.append(1)
        elif -key[i] in model_set:
            recovered_bits.append(0)
        else:
            recovered_bits.append(None)

    for i in unknown_bits:
        print(
            f"key[{i}]: "
            f"oczekiwany={key_bits[i]}, "
            f"odzyskany={recovered_bits[i]}"
        )
        assert recovered_bits[i] == key_bits[i]
    solver.delete()
    return {
        "status": "SAT",
        "time": lapse
    }

def get_new_nibbles():
    try:
        with open("analysis/used_pairs.json", "r") as file:
            used = json.load(file)
    except FileNotFoundError:
        used = []
    while True:
        nibbles = sorted(random.sample(range(32), UNKNOWN_NIBBLES_COUNT))
        if nibbles not in used:
            break
    used.append(nibbles)
    with open("analysis/used_pairs.json", "w") as file:
        json.dump(used, file)
    return nibbles

unknown_nibbles = get_new_nibbles()

def save_report(results, unknown_nibbles):
    times = []
    for result in results:
        times.append(result["time"])
    if len(times) > 0:
        mean = statistics.mean(times)
    else:
        mean = None
    if len(times) > 1:
        std = statistics.stdev(times)
    else:
        std = None
    sat_count = 0
    unsat_count = 0
    for result in results:
        if result["status"] == "SAT":
            sat_count += 1
        elif result["status"] == "UNSAT":
            unsat_count += 1
    nibble_name = "_".join(
        str(nibble)
        for nibble in unknown_nibbles
    )
    with open(
        f"wyniki_testow/testy_photon_{nibble_name}.md",
        "w"
    ) as file:
        file.write("# Wyniki eksperymentu\n\n")
        file.write("## Parametry\n\n")
        file.write(f"- Liczba nieznanych nibble: {UNKNOWN_NIBBLES_COUNT}\n")
        file.write(f"- Nieznane nibble: {unknown_nibbles}\n")
        file.write(f"- Liczba testow: {len(results)}\n")
        file.write(f"- SAT: {sat_count}\n")
        file.write(f"- UNSAT: {unsat_count}\n\n")
        file.write("## Czasy rozwiazania\n\n")
        if len(times) > 0:
            file.write(f"- Sredni czas: {mean:.3f} s\n")
            file.write(f"- Minimalny czas: {min(times):.3f} s\n")
            file.write(f"- Maksymalny czas: {max(times):.3f} s\n")
        if std is not None:
            file.write(f"- Odchylenie standardowe: {std:.3f} s\n")
        file.write("\n## Poszczegolne testy\n\n")
        file.write("| Test | Status | Czas [s] |\n")
        file.write("|---|---|---:|\n")
        for i, result in enumerate(results,start=1):
            file.write(f"| {i} | {result['status']} | {result['time']:.3f} |\n")

results = []

for i, sample in enumerate(samples):
    print(f"\n--- Proba "f"{i + 1}/{len(samples)} ---")
    result = analyze_sample(sample,unknown_nibbles)

    results.append(result)


save_report(results,unknown_nibbles)