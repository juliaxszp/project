import csv
import random
import sys
from itertools import product
from multiprocessing import get_context
from pathlib import Path
from queue import Empty
from time import perf_counter
from pysat.solvers import Kissat404, Cadical300, Glucose42, MapleChrono, Mergesat3
from .basics import BasicFunctions
from .gift_cofb import gift_cofb_encrypt

PROJECT_DIR = Path(__file__).resolve().parent.parent
UNKNOWN_COUNTS = [1, 2, 4, 8, 16, 20]
RANDOM_TRIALS = 3
RANDOM_SEED_BASE = 20260916
KAT_NAMES = ["count1", "count545", "count1089"]
UNIQUENESS_UNKNOWN_COUNT = 16
SOLVER_BENCHMARK_UNKNOWN_COUNT = 16
SOLVER_BENCHMARK_TRIAL = 1
SOLVER_TIMEOUT_SECONDS = 1800
DIVIDE_KAT = "count1089"
DIVIDE_UNKNOWN_COUNT = 20
DIVIDE_TRIAL = 1
DIVIDE_SPLIT_COUNTS = [2, 3, 4, 5]
DIVIDE_MAX_WORKERS = 4

SOLVERS = [
    ("Kissat404", Kissat404),
    ("Glucose42", Glucose42),
    ("MapleChrono", MapleChrono)
]

SOLVER_CLASSES = {
    "Kissat404": Kissat404,
    "Cadical300": Cadical300,
    "Glucose42": Glucose42,
    "MapleChrono": MapleChrono,
    "Mergesat3": Mergesat3
}

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
        recovered_key_hex = "" if recovered_key is None else recovered_key.hex().upper()
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
        recovered_key_hex = "" if recovered_key is None else recovered_key.hex().upper()
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
            if row["kat"] == kat_name and int(row["unknown_bits"]) == unknown_count and int(row["trial"]) == trial:
                return True

    return False

def save_uniqueness_result(case_name, kat_name, position_mode, trial, seed, unknown_count, unknown_positions, result, correct):
    results_file = get_results_file("unique")
    file_exists = results_file.exists()

    with open(results_file, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "case",
                "kat",
                "position_mode",
                "trial",
                "seed",
                "unknown_bits",
                "known_bits",
                "unknown_positions",
                "build_time",
                "solve_time",
                "uniqueness_time",
                "total_time",
                "correct",
                "unique",
                "recovered_key",
                "variables",
                "clauses"
            ])

        recovered_key = result["recovered_key"]
        recovered_key_hex = "" if recovered_key is None else recovered_key.hex().upper()
        positions_text = ";".join(str(position) for position in unknown_positions)

        writer.writerow([
            case_name,
            kat_name,
            position_mode,
            trial,
            seed,
            unknown_count,
            128 - unknown_count,
            positions_text,
            result["build_time"],
            result["solve_time"],
            result["uniqueness_time"],
            result["total_time"],
            correct,
            result["unique"],
            recovered_key_hex,
            result["variables"],
            result["clauses"]
        ])

def uniqueness_result_exists(case_name):
    results_file = get_results_file("unique")

    if not results_file.exists():
        return False

    with open(results_file, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["case"] == case_name:
                return True

    return False

def save_solver_result(kat_name, position_mode, trial, seed, unknown_count, unknown_positions, solver_name, build_time, solve_time, satisfiable, correct, recovered_key, variables, clauses, status, error_text):
    results_file = get_results_file("solvers")
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
                "solver",
                "build_time",
                "solve_time",
                "satisfiable",
                "correct",
                "recovered_key",
                "variables",
                "clauses",
                "status",
                "error"
            ])

        recovered_key_hex = "" if recovered_key is None else recovered_key.hex().upper()
        positions_text = ";".join(str(position) for position in unknown_positions)

        writer.writerow([
            kat_name,
            position_mode,
            trial,
            seed,
            unknown_count,
            128 - unknown_count,
            positions_text,
            solver_name,
            build_time,
            solve_time,
            satisfiable,
            correct,
            recovered_key_hex,
            variables,
            clauses,
            status,
            error_text
        ])

def solver_result_exists(kat_name, unknown_count, trial, solver_name):
    results_file = get_results_file("solvers")

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

            if row["solver"] != solver_name:
                continue

            return True

    return False

def solver_worker(solver_name, clauses, key_bits, true_key, result_queue):
    solver_class = SOLVER_CLASSES[solver_name]
    solve_start = perf_counter()

    try:
        with solver_class(bootstrap_with=clauses) as solver:
            satisfiable = solver.solve()

            if satisfiable:
                model = solver.get_model()
            else:
                model = None

        solve_time = perf_counter() - solve_start

        if satisfiable:
            recovered_key = sat_bits_to_bytes(key_bits, model)
            correct = recovered_key == true_key
        else:
            recovered_key = None
            correct = False

        result_queue.put({
            "status": "OK",
            "solve_time": solve_time,
            "satisfiable": satisfiable,
            "correct": correct,
            "recovered_key": recovered_key,
            "error": ""
        })

    except Exception as error:
        result_queue.put({
            "status": "ERROR",
            "solve_time": perf_counter() - solve_start,
            "satisfiable": False,
            "correct": False,
            "recovered_key": None,
            "error": str(error)
        })

def run_solver_with_timeout(solver_name, clauses, key_bits, true_key, timeout_seconds):
    context = get_context("fork")
    result_queue = context.Queue()

    process = context.Process(
        target=solver_worker,
        args=(
            solver_name,
            clauses,
            key_bits,
            true_key,
            result_queue
        )
    )

    wall_start = perf_counter()
    process.start()

    try:
        process.join(timeout_seconds)

    except KeyboardInterrupt:
        if process.is_alive():
            process.terminate()
            process.join()

        raise

    if process.is_alive():
        process.terminate()
        process.join()

        return {
            "status": "TIMEOUT",
            "solve_time": perf_counter() - wall_start,
            "satisfiable": False,
            "correct": False,
            "recovered_key": None,
            "error": f"Exceeded timeout of {timeout_seconds} seconds"
        }

    try:
        result = result_queue.get(timeout=5)

    except Empty:
        return {
            "status": "ERROR",
            "solve_time": perf_counter() - wall_start,
            "satisfiable": False,
            "correct": False,
            "recovered_key": None,
            "error": f"Solver process exited with code {process.exitcode} without returning a result"
        }

    return result

def get_random_baseline_solve_time(kat_name, unknown_count, trial):
    results_file = get_results_file("random")

    if not results_file.exists():
        return None

    with open(results_file, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["kat"] != kat_name:
                continue

            if int(row["unknown_bits"]) != unknown_count:
                continue

            if int(row["trial"]) != trial:
                continue

            return float(row["solve_time"])

    return None

def save_divide_row(row_type, experiment, kat_name, trial, seed, unknown_count, split_bits, split_positions, max_workers, branch_id, assignment, status, satisfiable, correct, recovered_key, solve_time, experiment_wall_time, baseline_solve_time, variables, clauses):
    results_file = get_results_file("divide")
    file_exists = results_file.exists()

    with open(results_file, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "row_type",
                "experiment",
                "kat",
                "position_mode",
                "trial",
                "seed",
                "unknown_bits",
                "known_bits",
                "split_bits",
                "split_positions",
                "max_workers",
                "branch_id",
                "assignment",
                "status",
                "satisfiable",
                "correct",
                "recovered_key",
                "solve_time",
                "experiment_wall_time",
                "baseline_solve_time",
                "variables",
                "clauses"
            ])

        split_positions_text = ";".join(str(position) for position in split_positions)
        assignment_text = "".join(str(bit) for bit in assignment) if assignment is not None else ""
        recovered_key_hex = "" if recovered_key is None else recovered_key.hex().upper()
        baseline_text = "" if baseline_solve_time is None else baseline_solve_time

        writer.writerow([
            row_type,
            experiment,
            kat_name,
            "random",
            trial,
            seed,
            unknown_count,
            128 - unknown_count,
            split_bits,
            split_positions_text,
            max_workers,
            branch_id,
            assignment_text,
            status,
            satisfiable,
            correct,
            recovered_key_hex,
            solve_time,
            experiment_wall_time,
            baseline_text,
            variables,
            clauses
        ])

def get_divide_completed_branches(experiment):
    results_file = get_results_file("divide")
    completed = set()

    if not results_file.exists():
        return completed

    with open(results_file, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["experiment"] != experiment:
                continue

            if row["row_type"] != "branch":
                continue

            if row["status"] not in ["SAT", "UNSAT"]:
                continue

            completed.add(row["branch_id"])

    return completed

def divide_summary_exists(experiment):
    results_file = get_results_file("divide")

    if not results_file.exists():
        return False

    with open(results_file, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["experiment"] != experiment:
                continue

            if row["row_type"] != "summary":
                continue

            if row["status"] in ["SAT_FOUND", "UNSAT_ALL"]:
                return True

    return False

def divide_branch_worker(branch_id, clauses, key_bits, true_key, result_queue):
    solve_start = perf_counter()

    try:
        with Kissat404(bootstrap_with=clauses) as solver:
            satisfiable = solver.solve()

            if satisfiable:
                model = solver.get_model()
            else:
                model = None

        solve_time = perf_counter() - solve_start

        if satisfiable:
            recovered_key = sat_bits_to_bytes(key_bits, model)
            correct = recovered_key == true_key
            status = "SAT"
        else:
            recovered_key = None
            correct = False
            status = "UNSAT"

        result_queue.put({
            "branch_id": branch_id,
            "status": status,
            "satisfiable": satisfiable,
            "correct": correct,
            "recovered_key": recovered_key,
            "solve_time": solve_time,
            "error": ""
        })

    except Exception as error:
        result_queue.put({
            "branch_id": branch_id,
            "status": "ERROR",
            "satisfiable": False,
            "correct": False,
            "recovered_key": None,
            "solve_time": perf_counter() - solve_start,
            "error": str(error)
        })

def terminate_processes(active_processes):
    for process in active_processes.values():
        if process.is_alive():
            process.terminate()

    for process in active_processes.values():
        process.join()

def run_divide_experiment(kat_name, unknown_count, trial, split_bits, max_workers, deadline):
    experiment = f"{kat_name}_random{trial}_{unknown_count}_split{split_bits}"

    if divide_summary_exists(experiment):
        print()
        print(experiment, "- ALREADY COMPLETED")
        return True

    case = get_kat_case(kat_name)
    seed = get_random_seed(unknown_count, trial)
    unknown_positions = get_unknown_positions(unknown_count, "random", seed)
    split_positions = unknown_positions[:split_bits]
    baseline_solve_time = get_random_baseline_solve_time(kat_name, unknown_count, trial)

    print()
    print("=====================================================")
    print("DIVIDE-AND-CONQUER EXPERIMENT")
    print("Experiment:", experiment)
    print("KAT:", kat_name)
    print("Unknown bits:", unknown_count)
    print("Trial:", trial)
    print("Seed:", seed)
    print("Split bits:", split_bits)
    print("Branches:", 2 ** split_bits)
    print("Split positions:", split_positions)
    print("Maximum parallel workers:", max_workers)

    if baseline_solve_time is not None:
        print("Single Kissat baseline:", f"{baseline_solve_time:.2f} s")

    print("=====================================================")
    print()
    print("Building base CNF...", flush=True)

    instance = build_key_recovery_instance(
        case["true_key"],
        unknown_positions,
        case["nonce"],
        case["associated_data"],
        case["message"],
        case["known_ciphertext"],
        case["known_tag"]
    )

    builder = instance["builder"]
    key_bits = instance["key_bits"]
    completed_branches = get_divide_completed_branches(experiment)
    assignments = list(product([0, 1], repeat=split_bits))
    pending = []

    for assignment in assignments:
        branch_id = "".join(str(bit) for bit in assignment)

        if branch_id in completed_branches:
            continue

        pending.append(assignment)

    print("Build time:", f'{instance["build_time"]:.2f} s')
    print("SAT variables:", instance["variables"])
    print("CNF clauses:", instance["clauses"])
    print("Already completed branches:", len(completed_branches))
    print("Remaining branches:", len(pending))
    print()

    if len(pending) == 0:
        print("All branches were already completed.")
        return True

    context = get_context("fork")
    result_queue = context.Queue()
    active_processes = {}
    active_assignments = {}
    experiment_start = perf_counter()

    try:
        while pending or active_processes:
            if perf_counter() >= deadline:
                print()
                print("Global night limit reached.")
                print("Stopping active branches.")
                terminate_processes(active_processes)
                return False

            while pending and len(active_processes) < max_workers:
                assignment = pending.pop(0)
                branch_id = "".join(str(bit) for bit in assignment)
                branch_units = []

                for position, value in zip(split_positions, assignment):
                    var = key_bits[position]
                    branch_units.append([var] if value == 1 else [-var])

                branch_clauses = builder.cnf.clauses + branch_units

                process = context.Process(
                    target=divide_branch_worker,
                    args=(
                        branch_id,
                        branch_clauses,
                        key_bits,
                        case["true_key"],
                        result_queue
                    )
                )

                process.start()
                active_processes[branch_id] = process
                active_assignments[branch_id] = assignment

                print(
                    "Started branch",
                    branch_id,
                    "assignment",
                    assignment,
                    flush=True
                )

            try:
                result = result_queue.get(timeout=1)

            except Empty:
                dead_branches = []

                for branch_id, process in active_processes.items():
                    if not process.is_alive():
                        dead_branches.append(branch_id)

                for branch_id in dead_branches:
                    process = active_processes.pop(branch_id)
                    process.join()
                    active_assignments.pop(branch_id)

                    print(
                        "Branch",
                        branch_id,
                        "ended without a result.",
                        flush=True
                    )

                continue

            branch_id = result["branch_id"]
            assignment = active_assignments.pop(branch_id)
            process = active_processes.pop(branch_id)
            process.join()

            experiment_wall_time = perf_counter() - experiment_start

            print()
            print(
                "Branch",
                branch_id,
                "|",
                result["status"],
                "|",
                f'{result["solve_time"]:.2f}s',
                "| correct:",
                result["correct"],
                flush=True
            )

            save_divide_row(
                "branch",
                experiment,
                kat_name,
                trial,
                seed,
                unknown_count,
                split_bits,
                split_positions,
                max_workers,
                branch_id,
                assignment,
                result["status"],
                result["satisfiable"],
                result["correct"],
                result["recovered_key"],
                result["solve_time"],
                experiment_wall_time,
                baseline_solve_time,
                instance["variables"],
                instance["clauses"]
            )

            if result["satisfiable"]:
                print()
                print("SAT branch found:", branch_id)
                print("Correct key:", result["correct"])
                print("Stopping all remaining branches.")

                terminate_processes(active_processes)

                experiment_wall_time = perf_counter() - experiment_start

                save_divide_row(
                    "summary",
                    experiment,
                    kat_name,
                    trial,
                    seed,
                    unknown_count,
                    split_bits,
                    split_positions,
                    max_workers,
                    branch_id,
                    assignment,
                    "SAT_FOUND",
                    True,
                    result["correct"],
                    result["recovered_key"],
                    result["solve_time"],
                    experiment_wall_time,
                    baseline_solve_time,
                    instance["variables"],
                    instance["clauses"]
                )

                print("Experiment wall time:", f"{experiment_wall_time:.2f} s")

                if baseline_solve_time is not None:
                    speedup = baseline_solve_time / experiment_wall_time
                    print("Speedup vs single Kissat:", f"{speedup:.2f}x")

                return True

        experiment_wall_time = perf_counter() - experiment_start

        save_divide_row(
            "summary",
            experiment,
            kat_name,
            trial,
            seed,
            unknown_count,
            split_bits,
            split_positions,
            max_workers,
            "",
            None,
            "UNSAT_ALL",
            False,
            False,
            None,
            0.0,
            experiment_wall_time,
            baseline_solve_time,
            instance["variables"],
            instance["clauses"]
        )

        print()
        print("All branches returned UNSAT.")
        return True

    except KeyboardInterrupt:
        print()
        print("Divide experiment interrupted by user.")
        terminate_processes(active_processes)
        print("Completed branches are already saved.")
        return False

def run_divide_night(hours):
    night_start = perf_counter()
    deadline = night_start + hours * 3600

    print()
    print("=====================================================")
    print("GIFT-COFB NIGHT DIVIDE-AND-CONQUER ANALYSIS")
    print("Maximum runtime:", hours, "hours")
    print("KAT:", DIVIDE_KAT)
    print("Unknown bits:", DIVIDE_UNKNOWN_COUNT)
    print("Trial:", DIVIDE_TRIAL)
    print("Split counts:", DIVIDE_SPLIT_COUNTS)
    print("Parallel Kissat workers:", DIVIDE_MAX_WORKERS)
    print("Results file:", get_results_file("divide"))
    print("=====================================================")

    for split_bits in DIVIDE_SPLIT_COUNTS:
        if perf_counter() >= deadline:
            print()
            print("Global night limit reached before next experiment.")
            break

        completed = run_divide_experiment(
            DIVIDE_KAT,
            DIVIDE_UNKNOWN_COUNT,
            DIVIDE_TRIAL,
            split_bits,
            DIVIDE_MAX_WORKERS,
            deadline
        )

        if not completed and perf_counter() >= deadline:
            break

        if not completed:
            print()
            print("Current experiment was not completed.")
            print("Run the same command later to resume.")
            break

    total_time = perf_counter() - night_start

    print()
    print("=====================================================")
    print("NIGHT DIVIDE ANALYSIS STOPPED")
    print("Runtime:", f"{total_time / 3600:.2f} h")
    print("Completed results are saved in:")
    print(get_results_file("divide"))
    print("Run the same command to resume.")
    print("=====================================================")

def run_position_analysis(kat_name, position_mode):
    case = get_kat_case(kat_name)

    for unknown_count in UNKNOWN_COUNTS:
        unknown_positions = get_unknown_positions(unknown_count, position_mode)

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

        recovered_key = result["recovered_key"]
        correct = recovered_key == case["true_key"]

        save_position_result(
            kat_name,
            position_mode,
            unknown_count,
            unknown_positions,
            result,
            correct
        )

def run_random_analysis(kat_name):
    case = get_kat_case(kat_name)

    for unknown_count in UNKNOWN_COUNTS:
        for trial in range(1, RANDOM_TRIALS + 1):
            if random_result_exists(kat_name, unknown_count, trial):
                continue

            seed = get_random_seed(unknown_count, trial)
            unknown_positions = get_unknown_positions(unknown_count, "random", seed)

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

            recovered_key = result["recovered_key"]
            correct = recovered_key == case["true_key"]

            save_random_result(
                kat_name,
                trial,
                seed,
                unknown_count,
                unknown_positions,
                result,
                correct
            )

def run_all_analysis(position_mode):
    for kat_name in KAT_NAMES:
        if position_mode == "random":
            run_random_analysis(kat_name)
        else:
            run_position_analysis(kat_name, position_mode)

def get_uniqueness_cases():
    cases = []

    for kat_name in KAT_NAMES:
        cases.append({
            "case_name": f"{kat_name}_last_{UNIQUENESS_UNKNOWN_COUNT}",
            "kat_name": kat_name,
            "position_mode": "last",
            "trial": 0,
            "seed": 0
        })

        cases.append({
            "case_name": f"{kat_name}_first_{UNIQUENESS_UNKNOWN_COUNT}",
            "kat_name": kat_name,
            "position_mode": "first",
            "trial": 0,
            "seed": 0
        })

        for trial in range(1, RANDOM_TRIALS + 1):
            cases.append({
                "case_name": f"{kat_name}_random_{UNIQUENESS_UNKNOWN_COUNT}_trial{trial}",
                "kat_name": kat_name,
                "position_mode": "random",
                "trial": trial,
                "seed": get_random_seed(UNIQUENESS_UNKNOWN_COUNT, trial)
            })

    return cases

def run_uniqueness_analysis():
    uniqueness_cases = get_uniqueness_cases()

    for uniqueness_case in uniqueness_cases:
        case_name = uniqueness_case["case_name"]
        kat_name = uniqueness_case["kat_name"]
        position_mode = uniqueness_case["position_mode"]
        trial = uniqueness_case["trial"]
        seed = uniqueness_case["seed"]

        if uniqueness_result_exists(case_name):
            continue

        case = get_kat_case(kat_name)

        if position_mode == "random":
            unknown_positions = get_unknown_positions(UNIQUENESS_UNKNOWN_COUNT, position_mode, seed)
        else:
            unknown_positions = get_unknown_positions(UNIQUENESS_UNKNOWN_COUNT, position_mode)

        result = recover_key_gift_cofb(
            true_key=case["true_key"],
            unknown_positions=unknown_positions,
            nonce=case["nonce"],
            associated_data=case["associated_data"],
            message=case["message"],
            known_ciphertext=case["known_ciphertext"],
            known_tag=case["known_tag"],
            check_unique=True
        )

        recovered_key = result["recovered_key"]
        correct = recovered_key == case["true_key"]

        save_uniqueness_result(
            case_name,
            kat_name,
            position_mode,
            trial,
            seed,
            UNIQUENESS_UNKNOWN_COUNT,
            unknown_positions,
            result,
            correct
        )

def run_solver_benchmark(kat_name="count1", unknown_count=SOLVER_BENCHMARK_UNKNOWN_COUNT, trial=SOLVER_BENCHMARK_TRIAL, timeout_seconds=SOLVER_TIMEOUT_SECONDS):
    case = get_kat_case(kat_name)
    seed = get_random_seed(unknown_count, trial)
    unknown_positions = get_unknown_positions(unknown_count, "random", seed)

    instance = build_key_recovery_instance(
        case["true_key"],
        unknown_positions,
        case["nonce"],
        case["associated_data"],
        case["message"],
        case["known_ciphertext"],
        case["known_tag"]
    )

    builder = instance["builder"]
    key_bits = instance["key_bits"]

    for solver_name, solver_class in SOLVERS:
        if solver_result_exists(kat_name, unknown_count, trial, solver_name):
            continue

        try:
            result = run_solver_with_timeout(
                solver_name,
                builder.cnf.clauses,
                key_bits,
                case["true_key"],
                timeout_seconds
            )

        except KeyboardInterrupt:
            return

        save_solver_result(
            kat_name,
            "random",
            trial,
            seed,
            unknown_count,
            unknown_positions,
            solver_name,
            instance["build_time"],
            result["solve_time"],
            result["satisfiable"],
            result["correct"],
            result["recovered_key"],
            instance["variables"],
            instance["clauses"],
            result["status"],
            result["error"]
        )

def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "divide-night":
        hours = 10.0

        if len(sys.argv) >= 3:
            hours = float(sys.argv[2])

        run_divide_night(hours)
        return

    if len(sys.argv) >= 2 and sys.argv[1] == "uniqueness":
        run_uniqueness_analysis()
        return

    if len(sys.argv) >= 2 and sys.argv[1] == "solvers":
        kat_name = "count1"
        unknown_count = SOLVER_BENCHMARK_UNKNOWN_COUNT
        trial = SOLVER_BENCHMARK_TRIAL
        timeout_seconds = SOLVER_TIMEOUT_SECONDS

        if len(sys.argv) >= 3:
            kat_name = sys.argv[2]

        if len(sys.argv) >= 4:
            unknown_count = int(sys.argv[3])

        if len(sys.argv) >= 5:
            trial = int(sys.argv[4])

        if len(sys.argv) >= 6:
            timeout_seconds = int(sys.argv[5])

        run_solver_benchmark(kat_name, unknown_count, trial, timeout_seconds)
        return

    if len(sys.argv) < 3:
        print("Usage:")
        print("python3 -m src.gift_cofb_analysis divide-night 10")
        print("python3 -m src.gift_cofb_analysis uniqueness")
        print("python3 -m src.gift_cofb_analysis solvers count1089 16 1 1800")
        print("python3 -m src.gift_cofb_analysis all random")
        return

    kat_name = sys.argv[1]
    position_mode = sys.argv[2]

    if kat_name == "all":
        run_all_analysis(position_mode)
        return

    if position_mode == "random":
        run_random_analysis(kat_name)
    else:
        run_position_analysis(kat_name, position_mode)

if __name__ == "__main__":
    main()