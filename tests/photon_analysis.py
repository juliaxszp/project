from pysat.solvers import Kissat404
from src.full_photon import *
from tests.test_photon import hex_to_sat 

def test_kpa265_no_ad():
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
    known_key_bits = 127
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
    print("variables:", builder.idp.top)
    print("clauses:", len(builder.cnf.clauses))
    solver = Kissat404()
    for clause in builder.cnf.clauses:
        solver.add_clause(clause)
    print("uruchamiany solver")
    import time
    start = time.time()
    result = solver.solve()
    lapse = time.time() - start
    print(result)
    print(f"lapse {lapse} s")
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
            f"expected={key_bits[i]}, "
            f"recovered={recovered_bits[i]}"
        )

        assert recovered_bits[i] == key_bits[i]