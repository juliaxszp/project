from pysat.solvers import Kissat404
from src.full_photon import *
from tests.test_photon import hex_to_sat 

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
    import random
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
    import random
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

if __name__ == "__main__":
    kpa454_with_ad_random()