import csv
import random
import sys
from itertools import product
from multiprocessing import get_context
from pathlib import Path
from queue import Empty
from time import perf_counter
from pysat.solvers import Kissat404
from .basics import BasicFunctions
from .gift_cofb import gift_cofb_encrypt

PROJECT_DIR = Path(__file__).resolve().parent.parent
RANDOM_RESULTS_FILE = PROJECT_DIR / "gift_cofb_analysis_results_random.csv"
NIGHT_RESULTS_FILE = PROJECT_DIR / "gift_cofb_analysis_results_divide_night.csv"
NIGHT_SUMMARY_FILE = PROJECT_DIR / "gift_cofb_analysis_results_divide_night_summary.csv"

RANDOM_SEED_BASE = 20260916
DIVIDE_SEED_BASE = 20260918

NIGHT_KAT = "count1089"
NIGHT_UNKNOWN_COUNT = 20
NIGHT_BASE_TRIAL = 1
WORKER_COUNTS = [1, 2, 4, 6, 8]
WORKER_TUNING_SPLIT_BITS = 5
WORKER_TUNING_DIVIDE_TRIAL = 1
SPLIT_COUNTS = [3, 4, 5, 6]
DIVIDE_TRIALS = [1, 2, 3]
GENERALIZATION_BASE_TRIALS = [2, 3]
CHALLENGE_UNKNOWN_COUNT = 22
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

def get_divide_seed(base_trial, divide_trial):
    return DIVIDE_SEED_BASE + base_trial * 100 + divide_trial

def get_divide_plan(unknown_positions, split_bits, base_trial, divide_trial):
    seed = get_divide_seed(base_trial, divide_trial)
    rng = random.Random(seed)

    position_order = list(unknown_positions)
    rng.shuffle(position_order)
    split_positions = sorted(position_order[:split_bits])

    assignments = list(product([0, 1], repeat=split_bits))
    rng.shuffle(assignments)

    return seed, split_positions, assignments

def night_header():
    return [
        "row_type",
        "phase",
        "experiment",
        "kat",
        "position_mode",
        "base_trial",
        "base_seed",
        "divide_trial",
        "divide_seed",
        "unknown_bits",
        "known_bits",
        "split_bits",
        "split_positions",
        "max_workers",
        "branch_id",
        "assignment",
        "branch_order",
        "status",
        "satisfiable",
        "correct",
        "recovered_key",
        "branch_solve_time",
        "experiment_wall_time",
        "baseline_solve_time",
        "variables",
        "clauses"
    ]

def save_night_row(row_type, phase, experiment, kat_name, base_trial, base_seed, divide_trial, divide_seed, unknown_count, split_bits, split_positions, max_workers, branch_id, assignment, branch_order, status, satisfiable, correct, recovered_key, branch_solve_time, experiment_wall_time, baseline_solve_time, variables, clauses):
    file_exists = NIGHT_RESULTS_FILE.exists()

    with open(NIGHT_RESULTS_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(night_header())

        split_positions_text = ";".join(str(position) for position in split_positions)
        assignment_text = "".join(str(bit) for bit in assignment) if assignment is not None else ""
        recovered_key_hex = "" if recovered_key is None else recovered_key.hex().upper()
        baseline_text = "" if baseline_solve_time is None else baseline_solve_time

        writer.writerow([
            row_type,
            phase,
            experiment,
            kat_name,
            "random",
            base_trial,
            base_seed,
            divide_trial,
            divide_seed,
            unknown_count,
            128 - unknown_count,
            split_bits,
            split_positions_text,
            max_workers,
            branch_id,
            assignment_text,
            branch_order,
            status,
            satisfiable,
            correct,
            recovered_key_hex,
            branch_solve_time,
            experiment_wall_time,
            baseline_text,
            variables,
            clauses
        ])

def read_night_rows():
    if not NIGHT_RESULTS_FILE.exists():
        return []

    with open(NIGHT_RESULTS_FILE, "r", newline="") as file:
        return list(csv.DictReader(file))

def get_experiment_rows(experiment):
    return [row for row in read_night_rows() if row["experiment"] == experiment]

def get_experiment_summary(experiment):
    for row in get_experiment_rows(experiment):
        if row["row_type"] == "summary" and row["status"] in ["SAT_FOUND", "UNSAT_ALL"]:
            return row

    return None

def get_experiment_sat_branch(experiment):
    for row in get_experiment_rows(experiment):
        if row["row_type"] == "branch" and row["status"] == "SAT":
            return row

    return None

def get_completed_branches(experiment):
    completed = set()

    for row in get_experiment_rows(experiment):
        if row["row_type"] != "branch":
            continue

        if row["status"] not in ["SAT", "UNSAT"]:
            continue

        completed.add(row["branch_id"])

    return completed

def get_previous_wall_time(experiment):
    maximum = 0.0

    for row in get_experiment_rows(experiment):
        value = row.get("experiment_wall_time", "")

        if value == "":
            continue

        try:
            maximum = max(maximum, float(value))
        except ValueError:
            pass

    return maximum

def refresh_summary_file():
    rows = []

    for row in read_night_rows():
        if row["row_type"] == "summary":
            rows.append(row)

    with open(NIGHT_SUMMARY_FILE, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=night_header())
        writer.writeheader()

        for row in rows:
            writer.writerow(row)

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
            "solve_time": solve_time
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

def make_experiment_name(kat_name, unknown_count, base_trial, split_bits, divide_trial, max_workers):
    return f"{kat_name}_random{base_trial}_{unknown_count}_split{split_bits}_divide{divide_trial}_workers{max_workers}"

def save_checkpoint(phase, experiment, kat_name, base_trial, base_seed, divide_trial, divide_seed, unknown_count, split_bits, split_positions, max_workers, total_wall_time, baseline_solve_time, variables, clauses, status):
    save_night_row(
        "checkpoint",
        phase,
        experiment,
        kat_name,
        base_trial,
        base_seed,
        divide_trial,
        divide_seed,
        unknown_count,
        split_bits,
        split_positions,
        max_workers,
        "",
        None,
        "",
        status,
        False,
        False,
        None,
        0.0,
        total_wall_time,
        baseline_solve_time,
        variables,
        clauses
    )

def run_divide_experiment(phase, kat_name, unknown_count, base_trial, split_bits, divide_trial, max_workers):
    experiment = make_experiment_name(
        kat_name,
        unknown_count,
        base_trial,
        split_bits,
        divide_trial,
        max_workers
    )

    existing_summary = get_experiment_summary(experiment)

    if existing_summary is not None:
        print()
        print(experiment, "- ALREADY COMPLETED")
        return existing_summary

    case = get_kat_case(kat_name)
    base_seed = get_random_seed(unknown_count, base_trial)
    unknown_positions = get_unknown_positions(unknown_count, "random", base_seed)

    divide_seed, split_positions, assignments = get_divide_plan(
        unknown_positions,
        split_bits,
        base_trial,
        divide_trial
    )

    true_assignment = tuple(
        key_bit_value(case["true_key"], position)
        for position in split_positions
    )

    true_branch_id = "".join(str(bit) for bit in true_assignment)

    assignment_order = {}

    for index, assignment in enumerate(assignments, start=1):
        branch_id = "".join(str(bit) for bit in assignment)
        assignment_order[branch_id] = index

    baseline_solve_time = get_random_baseline_solve_time(
        kat_name,
        unknown_count,
        base_trial
    )

    completed_branches = get_completed_branches(experiment)
    previous_wall_time = get_previous_wall_time(experiment)
    pending = []

    for assignment in assignments:
        branch_id = "".join(str(bit) for bit in assignment)

        if branch_id in completed_branches:
            continue

        pending.append(assignment)

    sat_branch = get_experiment_sat_branch(experiment)

    if sat_branch is not None:
        recovered_key_text = sat_branch["recovered_key"]
        recovered_key = bytes.fromhex(recovered_key_text) if recovered_key_text else None

        save_night_row(
            "summary",
            phase,
            experiment,
            kat_name,
            base_trial,
            base_seed,
            divide_trial,
            divide_seed,
            unknown_count,
            split_bits,
            split_positions,
            max_workers,
            sat_branch["branch_id"],
            tuple(int(bit) for bit in sat_branch["assignment"]),
            sat_branch["branch_order"],
            "SAT_FOUND",
            True,
            sat_branch["correct"] == "True",
            recovered_key,
            float(sat_branch["branch_solve_time"]),
            float(sat_branch["experiment_wall_time"]),
            baseline_solve_time,
            int(sat_branch["variables"]),
            int(sat_branch["clauses"])
        )

        refresh_summary_file()
        return get_experiment_summary(experiment)

    print()
    print("=====================================================")
    print("DIVIDE EXPERIMENT")
    print("Phase:", phase)
    print("Experiment:", experiment)
    print("Unknown bits:", unknown_count)
    print("Base trial:", base_trial)
    print("Split bits:", split_bits)
    print("Branches:", 2 ** split_bits)
    print("Workers:", max_workers)
    print("Divide trial:", divide_trial)
    print("Split positions:", split_positions)
    print("True branch:", true_branch_id)
    print("True branch order:", assignment_order[true_branch_id], "/", len(assignments))
    print("Completed branches:", len(completed_branches))
    print("Remaining branches:", len(pending))

    if baseline_solve_time is not None:
        print("Single Kissat baseline:", f"{baseline_solve_time:.2f} s")

    if previous_wall_time > 0:
        print("Previous recorded wall time:", f"{previous_wall_time:.2f} s")

    print("=====================================================")
    print()
    print("Building CNF...", flush=True)

    instance = build_key_recovery_instance(
        case["true_key"],
        unknown_positions,
        case["nonce"],
        case["associated_data"],
        case["message"],
        case["known_ciphertext"],
        case["known_tag"]
    )

    print("Build time:", f'{instance["build_time"]:.2f} s')
    print("Variables:", instance["variables"])
    print("Clauses:", instance["clauses"])
    print()

    if len(pending) == 0:
        total_wall_time = previous_wall_time

        save_night_row(
            "summary",
            phase,
            experiment,
            kat_name,
            base_trial,
            base_seed,
            divide_trial,
            divide_seed,
            unknown_count,
            split_bits,
            split_positions,
            max_workers,
            "",
            None,
            "",
            "UNSAT_ALL",
            False,
            False,
            None,
            0.0,
            total_wall_time,
            baseline_solve_time,
            instance["variables"],
            instance["clauses"]
        )

        refresh_summary_file()
        return get_experiment_summary(experiment)

    builder = instance["builder"]
    key_bits = instance["key_bits"]

    context = get_context("fork")
    result_queue = context.Queue()
    active_processes = {}
    active_assignments = {}

    session_start = perf_counter()
    last_checkpoint = session_start

    try:
        while pending or active_processes:
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
                    "| order",
                    assignment_order[branch_id],
                    flush=True
                )

            now = perf_counter()

            if now - last_checkpoint >= CHECKPOINT_SECONDS:
                total_wall_time = previous_wall_time + (now - session_start)

                save_checkpoint(
                    phase,
                    experiment,
                    kat_name,
                    base_trial,
                    base_seed,
                    divide_trial,
                    divide_seed,
                    unknown_count,
                    split_bits,
                    split_positions,
                    max_workers,
                    total_wall_time,
                    baseline_solve_time,
                    instance["variables"],
                    instance["clauses"],
                    "RUNNING"
                )

                last_checkpoint = now

            try:
                result = result_queue.get(timeout=1)

            except Empty:
                continue

            branch_id = result["branch_id"]

            if branch_id not in active_processes:
                continue

            assignment = active_assignments.pop(branch_id)
            process = active_processes.pop(branch_id)
            process.join()

            total_wall_time = previous_wall_time + (perf_counter() - session_start)

            print(
                "Branch",
                branch_id,
                "| order",
                assignment_order[branch_id],
                "|",
                result["status"],
                "|",
                f'{result["solve_time"]:.2f}s',
                "| correct:",
                result["correct"],
                flush=True
            )

            save_night_row(
                "branch",
                phase,
                experiment,
                kat_name,
                base_trial,
                base_seed,
                divide_trial,
                divide_seed,
                unknown_count,
                split_bits,
                split_positions,
                max_workers,
                branch_id,
                assignment,
                assignment_order[branch_id],
                result["status"],
                result["satisfiable"],
                result["correct"],
                result["recovered_key"],
                result["solve_time"],
                total_wall_time,
                baseline_solve_time,
                instance["variables"],
                instance["clauses"]
            )

            if result["status"] == "ERROR":
                print("A branch returned ERROR. Stopping this experiment.")
                terminate_processes(active_processes)

                save_checkpoint(
                    phase,
                    experiment,
                    kat_name,
                    base_trial,
                    base_seed,
                    divide_trial,
                    divide_seed,
                    unknown_count,
                    split_bits,
                    split_positions,
                    max_workers,
                    total_wall_time,
                    baseline_solve_time,
                    instance["variables"],
                    instance["clauses"],
                    "ERROR"
                )

                return None

            if result["satisfiable"]:
                terminate_processes(active_processes)
                total_wall_time = previous_wall_time + (perf_counter() - session_start)

                save_night_row(
                    "summary",
                    phase,
                    experiment,
                    kat_name,
                    base_trial,
                    base_seed,
                    divide_trial,
                    divide_seed,
                    unknown_count,
                    split_bits,
                    split_positions,
                    max_workers,
                    branch_id,
                    assignment,
                    assignment_order[branch_id],
                    "SAT_FOUND",
                    True,
                    result["correct"],
                    result["recovered_key"],
                    result["solve_time"],
                    total_wall_time,
                    baseline_solve_time,
                    instance["variables"],
                    instance["clauses"]
                )

                refresh_summary_file()

                print()
                print("SAT branch found:", branch_id)
                print("Branch order:", assignment_order[branch_id])
                print("Correct key:", result["correct"])
                print("Wall time:", f"{total_wall_time:.2f} s")

                if baseline_solve_time is not None:
                    speedup = baseline_solve_time / total_wall_time
                    print("Speedup vs single Kissat:", f"{speedup:.2f}x")

                return get_experiment_summary(experiment)

        total_wall_time = previous_wall_time + (perf_counter() - session_start)

        save_night_row(
            "summary",
            phase,
            experiment,
            kat_name,
            base_trial,
            base_seed,
            divide_trial,
            divide_seed,
            unknown_count,
            split_bits,
            split_positions,
            max_workers,
            "",
            None,
            "",
            "UNSAT_ALL",
            False,
            False,
            None,
            0.0,
            total_wall_time,
            baseline_solve_time,
            instance["variables"],
            instance["clauses"]
        )

        refresh_summary_file()
        return get_experiment_summary(experiment)

    except KeyboardInterrupt:
        total_wall_time = previous_wall_time + (perf_counter() - session_start)

        print()
        print("Stopping active branches...")

        terminate_processes(active_processes)

        save_checkpoint(
            phase,
            experiment,
            kat_name,
            base_trial,
            base_seed,
            divide_trial,
            divide_seed,
            unknown_count,
            split_bits,
            split_positions,
            max_workers,
            total_wall_time,
            baseline_solve_time,
            instance["variables"],
            instance["clauses"],
            "PAUSED"
        )

        print("Experiment paused.")
        print("Completed branches and wall time are saved.")
        print("Run the same command to resume.")
        return None

def summary_wall_time(kat_name, unknown_count, base_trial, split_bits, divide_trial, workers):
    experiment = make_experiment_name(
        kat_name,
        unknown_count,
        base_trial,
        split_bits,
        divide_trial,
        workers
    )

    summary = get_experiment_summary(experiment)

    if summary is None:
        return None

    return float(summary["experiment_wall_time"])

def choose_best_workers():
    results = []

    for workers in WORKER_COUNTS:
        wall_time = summary_wall_time(
            NIGHT_KAT,
            NIGHT_UNKNOWN_COUNT,
            NIGHT_BASE_TRIAL,
            WORKER_TUNING_SPLIT_BITS,
            WORKER_TUNING_DIVIDE_TRIAL,
            workers
        )

        if wall_time is not None:
            results.append((wall_time, workers))

    if len(results) != len(WORKER_COUNTS):
        return None

    results.sort()
    return results[0][1]

def choose_best_split(best_workers):
    split_results = []

    for split_bits in SPLIT_COUNTS:
        times = []

        for divide_trial in DIVIDE_TRIALS:
            wall_time = summary_wall_time(
                NIGHT_KAT,
                NIGHT_UNKNOWN_COUNT,
                NIGHT_BASE_TRIAL,
                split_bits,
                divide_trial,
                best_workers
            )

            if wall_time is not None:
                times.append(wall_time)

        if len(times) != len(DIVIDE_TRIALS):
            return None

        average_time = sum(times) / len(times)
        split_results.append((average_time, split_bits))

    split_results.sort()
    return split_results[0][1]

def print_worker_summary():
    baseline = get_random_baseline_solve_time(
        NIGHT_KAT,
        NIGHT_UNKNOWN_COUNT,
        NIGHT_BASE_TRIAL
    )

    print()
    print("WORKER SCALING SUMMARY")
    print("Workers | Wall time | Speedup")

    for workers in WORKER_COUNTS:
        wall_time = summary_wall_time(
            NIGHT_KAT,
            NIGHT_UNKNOWN_COUNT,
            NIGHT_BASE_TRIAL,
            WORKER_TUNING_SPLIT_BITS,
            WORKER_TUNING_DIVIDE_TRIAL,
            workers
        )

        if wall_time is None:
            print(workers, "| missing")
            continue

        if baseline is None:
            print(workers, "|", f"{wall_time:.2f}s")
        else:
            print(workers, "|", f"{wall_time:.2f}s", "|", f"{baseline / wall_time:.2f}x")

def print_split_summary(best_workers):
    print()
    print("SPLIT DEPTH SUMMARY")
    print("Split bits | Average wall time")

    for split_bits in SPLIT_COUNTS:
        times = []

        for divide_trial in DIVIDE_TRIALS:
            wall_time = summary_wall_time(
                NIGHT_KAT,
                NIGHT_UNKNOWN_COUNT,
                NIGHT_BASE_TRIAL,
                split_bits,
                divide_trial,
                best_workers
            )

            if wall_time is not None:
                times.append(wall_time)

        if len(times) == 0:
            print(split_bits, "| missing")
        else:
            print(split_bits, "|", f"{sum(times) / len(times):.2f}s", "| trials:", len(times))

def run_phase_worker_scaling():
    print()
    print("#####################################################")
    print("PHASE 1 - CLEAN WORKER SCALING")
    print("#####################################################")

    for workers in WORKER_COUNTS:
        result = run_divide_experiment(
            "worker_scaling",
            NIGHT_KAT,
            NIGHT_UNKNOWN_COUNT,
            NIGHT_BASE_TRIAL,
            WORKER_TUNING_SPLIT_BITS,
            WORKER_TUNING_DIVIDE_TRIAL,
            workers
        )

        if result is None:
            return False

    print_worker_summary()
    return True

def run_phase_split_depth(best_workers):
    print()
    print("#####################################################")
    print("PHASE 2 - SPLIT DEPTH")
    print("Workers:", best_workers)
    print("#####################################################")

    for split_bits in SPLIT_COUNTS:
        for divide_trial in DIVIDE_TRIALS:
            result = run_divide_experiment(
                "split_depth",
                NIGHT_KAT,
                NIGHT_UNKNOWN_COUNT,
                NIGHT_BASE_TRIAL,
                split_bits,
                divide_trial,
                best_workers
            )

            if result is None:
                return False

    print_split_summary(best_workers)
    return True

def run_phase_generalization(best_workers, best_split):
    print()
    print("#####################################################")
    print("PHASE 3 - OTHER RANDOM 20-BIT INSTANCES")
    print("Workers:", best_workers)
    print("Split bits:", best_split)
    print("#####################################################")

    for base_trial in GENERALIZATION_BASE_TRIALS:
        for divide_trial in DIVIDE_TRIALS:
            result = run_divide_experiment(
                "generalization20",
                NIGHT_KAT,
                NIGHT_UNKNOWN_COUNT,
                base_trial,
                best_split,
                divide_trial,
                best_workers
            )

            if result is None:
                return False

    return True

def run_phase_challenge22(best_workers, best_split):
    print()
    print("#####################################################")
    print("PHASE 4 - 22 UNKNOWN BITS CHALLENGE")
    print("Workers:", best_workers)
    print("Split bits:", best_split)
    print("#####################################################")

    for divide_trial in DIVIDE_TRIALS:
        result = run_divide_experiment(
            "challenge22",
            NIGHT_KAT,
            CHALLENGE_UNKNOWN_COUNT,
            CHALLENGE_BASE_TRIAL,
            best_split,
            divide_trial,
            best_workers
        )

        if result is None:
            return False

    return True

def print_final_summary(best_workers, best_split):
    print()
    print("=====================================================")
    print("NIGHT STUDY FINISHED")
    print("Best workers from tuning:", best_workers)
    print("Best split bits from 20-bit study:", best_split)
    print("Full results:", NIGHT_RESULTS_FILE)
    print("Summary results:", NIGHT_SUMMARY_FILE)
    print("=====================================================")

def run_night_study():
    print()
    print("=====================================================")
    print("GIFT-COFB DIVIDE-AND-CONQUER NIGHT STUDY")
    print("NO TIME LIMIT")
    print()
    print("Phase 1: clean worker scaling 1/2/4/6/8")
    print("Phase 2: split depth 3/4/5/6, three randomized trials")
    print("Phase 3: random20 base trials 2 and 3")
    print("Phase 4: 22 unknown bits challenge")
    print()
    print("Press Ctrl+C whenever you need to stop.")
    print("Run the same command later to resume.")
    print("Checkpoint every:", CHECKPOINT_SECONDS, "seconds")
    print("=====================================================")

    if not run_phase_worker_scaling():
        return

    best_workers = choose_best_workers()

    if best_workers is None:
        print("Could not determine best worker count yet.")
        return

    print()
    print("Selected workers for next phases:", best_workers)

    if not run_phase_split_depth(best_workers):
        return

    best_split = choose_best_split(best_workers)

    if best_split is None:
        print("Could not determine best split depth yet.")
        return

    print()
    print("Selected split bits for next phases:", best_split)

    if not run_phase_generalization(best_workers, best_split):
        return

    if not run_phase_challenge22(best_workers, best_split):
        return

    print_final_summary(best_workers, best_split)

def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "night-study":
        run_night_study()
        return

    if len(sys.argv) >= 2 and sys.argv[1] == "status":
        print_worker_summary()

        best_workers = choose_best_workers()

        if best_workers is not None:
            print()
            print("Current best workers:", best_workers)
            print_split_summary(best_workers)

            best_split = choose_best_split(best_workers)

            if best_split is not None:
                print("Current best split bits:", best_split)

        return

    print("Usage:")
    print("python3 -m src.gift_cofb_analysis night-study")
    print("python3 -m src.gift_cofb_analysis status")

if __name__ == "__main__":
    main()