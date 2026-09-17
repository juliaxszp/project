import csv
import random
import sys
from pathlib import Path
from time import perf_counter
from pysat.solvers import Kissat404
from .basics import BasicFunctions
from .gift_cofb import gift_cofb_encrypt

PROJECT_DIR = Path(__file__).resolve().parent.parent
UNKNOWN_COUNTS = [1, 2, 4, 8, 16, 20]
RANDOM_TRIALS = 3
RANDOM_SEED_BASE = 20260916
KAT_NAMES = ["count1", "count545", "count1089"]

def get_results_file(position_mode):
    return PROJECT_DIR / f"gift_cofb_analysis_results_{position_mode}.csv"

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

    unknown_positions = set(unknown_positions)

    for position in unknown_positions:
        if position < 0 or position >= 128:
            raise ValueError("Key bit position must be between 0 and 127")

    key_bits = []
    bit_position = 0

    for byte in true_key:
        for bit_index in range(7, -1, -1):
            var = builder.var(f"{prefix}_{bit_position}")
            key_bits.append(var)

            if bit_position not in unknown_positions:
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

def recover_key_gift_cofb(true_key, unknown_positions, nonce, associated_data, message, known_ciphertext, known_tag, check_unique=True):
    total_start = perf_counter()
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

    number_of_variables = builder.idp.top
    number_of_clauses = len(builder.cnf.clauses)

    solve_start = perf_counter()

    with Kissat404(bootstrap_with=builder.cnf.clauses) as solver:
        satisfiable = solver.solve()
        solve_time = perf_counter() - solve_start

        if not satisfiable:
            total_time = perf_counter() - total_start

            return {
                "recovered_key": None,
                "build_time": build_time,
                "solve_time": solve_time,
                "uniqueness_time": 0.0,
                "total_time": total_time,
                "unique": False,
                "variables": number_of_variables,
                "clauses": number_of_clauses
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
        "build_time": build_time,
        "solve_time": solve_time,
        "uniqueness_time": uniqueness_time,
        "total_time": total_time,
        "unique": unique,
        "variables": number_of_variables,
        "clauses": number_of_clauses
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

def save_position_result(kat_name, position_mode, unknown_count, unknown_positions, result, correct):
    results_file = get_results_file(position_mode)
    file_exists = results_file.exists()

    with open(results_file, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "kat",
                "position_mode",
                "unknown_bits",
                "known_bits",
                "unknown_positions",
                "build_time",
                "solve_time",
                "total_time",
                "correct",
                "recovered_key",
                "variables",
                "clauses"
            ])

        recovered_key = result["recovered_key"]

        if recovered_key is None:
            recovered_key_hex = ""
        else:
            recovered_key_hex = recovered_key.hex().upper()

        positions_text = ";".join(str(position) for position in unknown_positions)

        writer.writerow([
            kat_name,
            position_mode,
            unknown_count,
            128 - unknown_count,
            positions_text,
            result["build_time"],
            result["solve_time"],
            result["total_time"],
            correct,
            recovered_key_hex,
            result["variables"],
            result["clauses"]
        ])

def save_random_result(kat_name, trial, seed, unknown_count, unknown_positions, result, correct):
    results_file = get_results_file("random")
    file_exists = results_file.exists()

    with open(results_file, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "kat",
                "position_mode",
                "trial",
                "seed",
                "unknown_bits",
                "known_bits",
                "unknown_positions",
                "build_time",
                "solve_time",
                "total_time",
                "correct",
                "recovered_key",
                "variables",
                "clauses"
            ])

        recovered_key = result["recovered_key"]

        if recovered_key is None:
            recovered_key_hex = ""
        else:
            recovered_key_hex = recovered_key.hex().upper()

        positions_text = ";".join(str(position) for position in unknown_positions)

        writer.writerow([
            kat_name,
            "random",
            trial,
            seed,
            unknown_count,
            128 - unknown_count,
            positions_text,
            result["build_time"],
            result["solve_time"],
            result["total_time"],
            correct,
            recovered_key_hex,
            result["variables"],
            result["clauses"]
        ])

def random_result_exists(kat_name, unknown_count, trial):
    results_file = get_results_file("random")

    if not results_file.exists():
        return False

    with open(results_file, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["kat"] != kat_name:
                continue

            if int(row["unknown_bits"]) != unknown_count:
                continue

            if int(row["trial"]) != trial:
                continue

            return True

    return False

def run_position_analysis(kat_name, position_mode):
    case = get_kat_case(kat_name)
    results_file = get_results_file(position_mode)

    print()
    print("GIFT-COFB KEY POSITION ANALYSIS")
    print("KAT:", kat_name)
    print("Position mode:", position_mode)
    print("Unknown counts:", UNKNOWN_COUNTS)
    print("Results file:", results_file)
    print()
    print("UNKNOWN | KNOWN | BUILD | SOLVE | TOTAL | CORRECT")
    print("-----------------------------------------------------")

    for unknown_count in UNKNOWN_COUNTS:
        unknown_positions = get_unknown_positions(unknown_count, position_mode)

        print()
        print(
            f"Running {unknown_count} unknown bits "
            f"({128 - unknown_count} known), "
            f"mode={position_mode}...",
            flush=True
        )

        try:
            result = recover_key_gift_cofb(
                true_key=case["true_key"],
                unknown_positions=unknown_positions,
                nonce=case["nonce"],
                associated_data=case["associated_data"],
                message=case["message"],
                known_ciphertext=case["known_ciphertext"],
                known_tag=case["known_tag"],
                check_unique=False
            )

        except Exception as error:
            if "keyboard interrupt" in str(error).lower():
                print()
                print("Analysis stopped by user.")
                print("Completed results are already saved.")
                return False

            raise

        recovered_key = result["recovered_key"]
        correct = recovered_key == case["true_key"]

        print(
            f"{unknown_count:7} | "
            f"{128 - unknown_count:5} | "
            f"{result['build_time']:5.2f}s | "
            f"{result['solve_time']:7.2f}s | "
            f"{result['total_time']:7.2f}s | "
            f"{correct}",
            flush=True
        )

        save_position_result(
            kat_name,
            position_mode,
            unknown_count,
            unknown_positions,
            result,
            correct
        )

        if recovered_key is None:
            print()
            print("No satisfying key was found.")
            return False

    print()
    print("Finished all selected unknown-bit counts.")
    return True

def run_random_analysis(kat_name):
    case = get_kat_case(kat_name)
    results_file = get_results_file("random")

    print()
    print("=====================================================")
    print("GIFT-COFB RANDOM KEY POSITION ANALYSIS")
    print("KAT:", kat_name)
    print("Trials:", RANDOM_TRIALS)
    print("Unknown counts:", UNKNOWN_COUNTS)
    print("Results file:", results_file)
    print("=====================================================")
    print()

    print("UNKNOWN | TRIAL | KNOWN | BUILD | SOLVE | TOTAL | CORRECT")
    print("------------------------------------------------------------")

    for unknown_count in UNKNOWN_COUNTS:
        for trial in range(1, RANDOM_TRIALS + 1):
            if random_result_exists(kat_name, unknown_count, trial):
                print(
                    f"{unknown_count:7} | "
                    f"{trial:5} | "
                    f"{128 - unknown_count:5} | "
                    f"ALREADY COMPLETED",
                    flush=True
                )

                continue

            seed = get_random_seed(unknown_count, trial)
            unknown_positions = get_unknown_positions(
                unknown_count,
                "random",
                seed
            )

            print()
            print(
                f"Running {unknown_count} random unknown bits, "
                f"trial {trial}/{RANDOM_TRIALS}, "
                f"seed={seed}...",
                flush=True
            )

            print(
                "Positions:",
                unknown_positions,
                flush=True
            )

            try:
                result = recover_key_gift_cofb(
                    true_key=case["true_key"],
                    unknown_positions=unknown_positions,
                    nonce=case["nonce"],
                    associated_data=case["associated_data"],
                    message=case["message"],
                    known_ciphertext=case["known_ciphertext"],
                    known_tag=case["known_tag"],
                    check_unique=False
                )

            except Exception as error:
                if "keyboard interrupt" in str(error).lower():
                    print()
                    print("Analysis stopped by user.")
                    print("All completed random results are already saved in:")
                    print(results_file)
                    return False

                raise

            recovered_key = result["recovered_key"]
            correct = recovered_key == case["true_key"]

            print(
                f"{unknown_count:7} | "
                f"{trial:5} | "
                f"{128 - unknown_count:5} | "
                f"{result['build_time']:5.2f}s | "
                f"{result['solve_time']:7.2f}s | "
                f"{result['total_time']:7.2f}s | "
                f"{correct}",
                flush=True
            )

            save_random_result(
                kat_name,
                trial,
                seed,
                unknown_count,
                unknown_positions,
                result,
                correct
            )

            if recovered_key is None:
                print()
                print("No satisfying key was found.")
                print("Stopping this KAT.")
                return False

            if not correct:
                print()
                print("Solver found a different compatible key.")
                print("The result was saved.")
                print("Analysis will continue.")

    print()
    print("Finished random analysis for:", kat_name)
    return True

def run_all_analysis(position_mode):
    print()
    print("GIFT-COFB FULL ANALYSIS")
    print("Position mode:", position_mode)
    print("KATs:", KAT_NAMES)
    print()

    for kat_name in KAT_NAMES:
        if position_mode == "random":
            completed = run_random_analysis(kat_name)
        else:
            completed = run_position_analysis(kat_name, position_mode)

        if not completed:
            print()
            print("Full analysis stopped.")
            return

    print()
    print("=====================================================")
    print("ALL ANALYSES FINISHED")
    print("=====================================================")

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("python3 -m src.gift_cofb_analysis count1 random")
        print("python3 -m src.gift_cofb_analysis count545 random")
        print("python3 -m src.gift_cofb_analysis count1089 random")
        print()
        print("Run all KATs automatically:")
        print("python3 -m src.gift_cofb_analysis all random")
        print()
        print("Position modes:")
        print("first")
        print("last")
        print("random")
        print()
        print("Unknown counts:")
        print(UNKNOWN_COUNTS)
        print()
        print("Random trials:")
        print(RANDOM_TRIALS)
        return

    kat_name = sys.argv[1]
    position_mode = sys.argv[2]

    if position_mode not in ["first", "last", "random"]:
        raise ValueError("Position mode must be: first, last or random")

    if kat_name == "all":
        run_all_analysis(position_mode)
        return

    if kat_name not in KAT_NAMES:
        raise ValueError("KAT must be: count1, count545, count1089 or all")

    if position_mode == "random":
        run_random_analysis(kat_name)
    else:
        run_position_analysis(kat_name, position_mode)

if __name__ == "__main__":
    main()