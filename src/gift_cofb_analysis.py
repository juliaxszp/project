"""
Common SAT-analysis utilities for GIFT-COFB key recovery.

This module contains the reusable part of the analysis: KAT definitions,
construction of partially unknown keys, CNF generation, key recovery with
Kissat, uniqueness checking helpers and deterministic FIRST/LAST/RANDOM
selection of unknown key positions.

The final parallel divide-and-conquer benchmark is intentionally kept in
``gift_cofb_divide_curve.py``.  Keeping the reusable SAT model here and the
long-running experiment runner separately makes the origin of the CSV files
easier to follow.

Main result families:
- gift_cofb_analysis_results_last.csv   - single-Kissat LAST baseline
- gift_cofb_analysis_results_first.csv  - FIRST-position experiments
- gift_cofb_analysis_results_random.csv - deterministic RANDOM experiments
- gift_cofb_analysis_results_unique.csv - uniqueness checks
- gift_cofb_analysis_results_solvers.csv - solver comparison
- gift_cofb_analysis_results_divide_*.csv - divide-and-conquer studies

See ``analysis/gift_cofb/README.md`` for the complete experiment history and the role of
each result file.
"""

import csv
import random
import sys
from pathlib import Path
from time import perf_counter
from pysat.solvers import Kissat404
from .basics import BasicFunctions
from .gift_cofb import gift_cofb_encrypt

PROJECT_DIR = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = PROJECT_DIR / "analysis" / "gift_cofb"
BASELINE_RESULTS_DIR = ANALYSIS_DIR / "results" / "baseline"
BASELINE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RANDOM_RESULTS_FILE = BASELINE_RESULTS_DIR / "gift_cofb_analysis_results_random.csv"
RANDOM_SEED_BASE = 20260916

CHALLENGE_BASE_TRIAL = 1
CHECKPOINT_SECONDS = 300

def bytes_to_fixed_sat_bits(builder, data, prefix):
    bits = []

    for byte_index, byte in enumerate(data):
        for bit_index in range(7, -1, -1):
            var = builder.var(f"{prefix}_{byte_index}_{bit_index}")
            bits.append(var)

            bit = (byte >> bit_index) & 1

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

    return bits

def key_to_sat_bits_with_unknowns(builder, true_key, unknown_positions, prefix="recovery_key"):
    if len(true_key) != 16:
        raise ValueError("GIFT-COFB key must contain 16 bytes")

    unknown_positions_set = set(unknown_positions)

    for position in unknown_positions_set:
        if position < 0 or position >= 128:
            raise ValueError("Key bit position must be between 0 and 127")

    key_bits = []
    bit_position = 0

    for byte in true_key:
        for bit_index in range(7, -1, -1):
            var = builder.var(f"{prefix}_{bit_position}")
            key_bits.append(var)

            if bit_position not in unknown_positions_set:
                bit = (byte >> bit_index) & 1

                if bit == 1:
                    builder.cnf.append([var])
                else:
                    builder.cnf.append([-var])

            bit_position += 1

    return key_bits

def constrain_sat_bits_to_bytes(builder, bits, expected):
    if len(bits) != len(expected) * 8:
        raise ValueError("Number of SAT bits does not match expected byte length")

    position = 0

    for byte in expected:
        for bit_index in range(7, -1, -1):
            bit = (byte >> bit_index) & 1
            var = bits[position]

            if bit == 1:
                builder.cnf.append([var])
            else:
                builder.cnf.append([-var])

            position += 1

def sat_bits_to_bytes(bits, model):
    model_set = set(model)
    result = bytearray()

    for start in range(0, len(bits), 8):
        value = 0

        for var in bits[start:start + 8]:
            value <<= 1

            if var in model_set:
                value |= 1

        result.append(value)

    return bytes(result)

def build_key_recovery_instance(true_key, unknown_positions, nonce, associated_data, message, known_ciphertext, known_tag):
    build_start = perf_counter()
    builder = BasicFunctions()

    key_bits = key_to_sat_bits_with_unknowns(builder, true_key, unknown_positions, "recovery_key")
    nonce_bits = bytes_to_fixed_sat_bits(builder, nonce, "recovery_nonce")
    associated_data_bits = bytes_to_fixed_sat_bits(builder, associated_data, "recovery_ad")
    message_bits = bytes_to_fixed_sat_bits(builder, message, "recovery_message")

    ciphertext_bits, tag_bits = gift_cofb_encrypt(
        builder,
        nonce_bits,
        associated_data_bits,
        message_bits,
        key_bits,
        "recovery_gift_cofb"
    )

    constrain_sat_bits_to_bytes(builder, ciphertext_bits, known_ciphertext)
    constrain_sat_bits_to_bytes(builder, tag_bits, known_tag)

    build_time = perf_counter() - build_start

    return {
        "builder": builder,
        "key_bits": key_bits,
        "build_time": build_time,
        "variables": builder.idp.top,
        "clauses": len(builder.cnf.clauses)
    }

def recover_key_gift_cofb(true_key, unknown_positions, nonce, associated_data, message, known_ciphertext, known_tag, check_unique=True):
    total_start = perf_counter()

    instance = build_key_recovery_instance(
        true_key,
        unknown_positions,
        nonce,
        associated_data,
        message,
        known_ciphertext,
        known_tag
    )

    builder = instance["builder"]
    key_bits = instance["key_bits"]

    solve_start = perf_counter()

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        satisfiable = solver.solve()
        solve_time = perf_counter() - solve_start

        if not satisfiable:
            total_time = perf_counter() - total_start

            return {
                "recovered_key": None,
                "build_time": instance["build_time"],
                "solve_time": solve_time,
                "uniqueness_time": 0.0,
                "total_time": total_time,
                "unique": False,
                "variables": instance["variables"],
                "clauses": instance["clauses"]
            }

        model = solver.get_model()

    model_set = set(model)
    recovered_key = sat_bits_to_bytes(key_bits, model)

    uniqueness_time = 0.0
    unique = None

    if check_unique:
        blocking_clause = []

        for var in key_bits:
            if var in model_set:
                blocking_clause.append(-var)
            else:
                blocking_clause.append(var)

        second_clauses = builder.cnf.clauses + [blocking_clause]
        uniqueness_start = perf_counter()

        with Kissat404(bootstrap_with=second_clauses) as second_solver:
            second_solution = second_solver.solve()

        uniqueness_time = perf_counter() - uniqueness_start
        unique = not second_solution

    total_time = perf_counter() - total_start

    return {
        "recovered_key": recovered_key,
        "build_time": instance["build_time"],
        "solve_time": solve_time,
        "uniqueness_time": uniqueness_time,
        "total_time": total_time,
        "unique": unique,
        "variables": instance["variables"],
        "clauses": instance["clauses"]
    }

def get_kat_case(kat_name):
    true_key = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
    nonce = bytes.fromhex("000102030405060708090A0B0C0D0E0F")

    if kat_name == "count1":
        return {
            "name": "count1",
            "true_key": true_key,
            "nonce": nonce,
            "associated_data": b"",
            "message": b"",
            "known_ciphertext": b"",
            "known_tag": bytes.fromhex("368965836D36614DE2FC24D0F801B9AF")
        }

    if kat_name == "count545":
        return {
            "name": "count545",
            "true_key": true_key,
            "nonce": nonce,
            "associated_data": bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
            "message": bytes.fromhex("000102030405060708090A0B0C0D0E0F"),
            "known_ciphertext": bytes.fromhex("3BFF715A56CBA49D1F7AC0691A966FDC"),
            "known_tag": bytes.fromhex("BF77814044BF3FC9A9DEBBD393F545D4")
        }

    if kat_name == "count1089":
        return {
            "name": "count1089",
            "true_key": true_key,
            "nonce": nonce,
            "associated_data": bytes.fromhex(
                "000102030405060708090A0B0C0D0E0F"
                "101112131415161718191A1B1C1D1E1F"
            ),
            "message": bytes.fromhex(
                "000102030405060708090A0B0C0D0E0F"
                "101112131415161718191A1B1C1D1E1F"
            ),
            "known_ciphertext": bytes.fromhex(
                "BAF563C60FBEDDC5662995F4C678BE80"
                "A7F7DE9B3AD8C97AA6CA17016D2AE650"
            ),
            "known_tag": bytes.fromhex("8E6FB3F79B412A1627AB7DFA755E0A22")
        }

    raise ValueError("Unknown KAT. Use: count1, count545 or count1089")

def get_random_seed(unknown_count, trial):
    return RANDOM_SEED_BASE + unknown_count * 100 + trial

def get_unknown_positions(unknown_count, position_mode, seed=None):
    if position_mode == "first":
        return list(range(0, unknown_count))

    if position_mode == "last":
        return list(range(128 - unknown_count, 128))

    if position_mode == "random":
        if seed is None:
            raise ValueError("Random mode requires a seed")

        rng = random.Random(seed)
        return sorted(rng.sample(range(128), unknown_count))

    raise ValueError("Unknown position mode. Use: first, last or random")

def get_random_baseline_solve_time(kat_name, unknown_count, trial):
    if not RANDOM_RESULTS_FILE.exists():
        return None

    with open(RANDOM_RESULTS_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row.get("kat") != kat_name:
                continue

            if int(row.get("unknown_bits", -1)) != unknown_count:
                continue

            if int(row.get("trial", -1)) != trial:
                continue

            return float(row["solve_time"])

    return None

def key_bit_value(key, position):
    byte_index = position // 8
    bit_index = 7 - (position % 8)
    return (key[byte_index] >> bit_index) & 1

def print_analysis_info():
    print()
    print("GIFT-COFB SAT ANALYSIS CORE")
    print("===========================")
    print("KAT cases: count1, count545, count1089")
    print("Unknown-position modes: first, last, random")
    print("Random seed base:", RANDOM_SEED_BASE)
    print()
    print("This file contains reusable key-recovery functions.")
    print("Final divide-and-conquer runner:")
    print("  python3 -m src.gift_cofb_divide_curve run")
    print()
    print("Full result provenance: analysis/gift_cofb/README.md")

def run_smoke_test():
    case = get_kat_case("count1")
    unknown_positions = get_unknown_positions(1, "last")
    result = recover_key_gift_cofb(
        case["true_key"],
        unknown_positions,
        case["nonce"],
        case["associated_data"],
        case["message"],
        case["known_ciphertext"],
        case["known_tag"],
        check_unique=False
    )
    recovered_key = result["recovered_key"]
    print("Recovered key:", recovered_key.hex().upper() if recovered_key else None)
    print("Correct:", recovered_key == case["true_key"])
    print("Solve time:", f'{result["solve_time"]:.4f}s')

def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "smoke":
        run_smoke_test()
        return

    print_analysis_info()
    print("Usage:")
    print("python3 -m src.gift_cofb_analysis")
    print("python3 -m src.gift_cofb_analysis smoke")

if __name__ == "__main__":
    main()
