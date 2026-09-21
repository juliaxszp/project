"""
Final parallel divide-and-conquer benchmark for GIFT-COFB key recovery.

Configuration used for the final comparison:
- KAT: Count1089
- unknown key positions: LAST
- unknown-bit counts: 8, 10, 12, 14, 16, 18, 20, 21, 22, 24
- split depth: 5 bits, therefore 32 branches
- maximum parallel Kissat workers: 8
- three deterministic randomized divide trials per point

The runner writes every completed branch to CSV, checkpoints long experiments
and can resume after Ctrl+C.  The summary CSV is the main source for the final
Single-Kissat vs divide-and-conquer plots.

Run:
    caffeinate -i python3 -m src.gift_cofb_divide_curve run

Status:
    python3 -m src.gift_cofb_divide_curve status
"""

import csv
import random
import sys
from itertools import product
from multiprocessing import get_context
from pathlib import Path
from queue import Empty
from time import perf_counter
from pysat.solvers import Kissat404
from .gift_cofb_analysis import build_key_recovery_instance, get_kat_case, get_unknown_positions, key_bit_value, sat_bits_to_bytes

PROJECT_DIR = Path(__file__).resolve().parent.parent
ANALYSIS_DIR = PROJECT_DIR / "analysis" / "gift_cofb"
BASELINE_RESULTS_DIR = ANALYSIS_DIR / "results" / "baseline"
DIVIDE_RESULTS_DIR = ANALYSIS_DIR / "results" / "divide"
BASELINE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DIVIDE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
BASELINE_LAST_FILE = BASELINE_RESULTS_DIR / "gift_cofb_analysis_results_last.csv"
CURVE_RESULTS_FILE = DIVIDE_RESULTS_DIR / "gift_cofb_analysis_results_divide_curve.csv"
CURVE_SUMMARY_FILE = DIVIDE_RESULTS_DIR / "gift_cofb_analysis_results_divide_curve_summary.csv"

KAT_NAME = "count1089"
UNKNOWN_COUNTS = [8, 10, 12, 14, 16, 18, 20, 21, 22, 24]
SPLIT_BITS = 5
MAX_WORKERS = 8
DIVIDE_TRIALS = [1, 2, 3]
DIVIDE_SEED_BASE = 20260919
CHECKPOINT_SECONDS = 300

def get_baseline_last_solve_time(unknown_count):
    if not BASELINE_LAST_FILE.exists():
        return None

    with open(BASELINE_LAST_FILE, "r", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row.get("kat") != KAT_NAME:
                continue

            if int(row.get("unknown_bits", -1)) != unknown_count:
                continue

            return float(row["solve_time"])

    return None

def get_divide_seed(unknown_count, divide_trial):
    return DIVIDE_SEED_BASE + unknown_count * 100 + divide_trial

def get_divide_plan(unknown_positions, unknown_count, divide_trial):
    divide_seed = get_divide_seed(unknown_count, divide_trial)
    rng = random.Random(divide_seed)

    position_order = list(unknown_positions)
    rng.shuffle(position_order)
    split_positions = sorted(position_order[:SPLIT_BITS])

    assignments = list(product([0, 1], repeat=SPLIT_BITS))
    rng.shuffle(assignments)

    return divide_seed, split_positions, assignments

def curve_header():
    return [
        "row_type",
        "experiment",
        "kat",
        "position_mode",
        "unknown_bits",
        "known_bits",
        "split_bits",
        "split_positions",
        "max_workers",
        "divide_trial",
        "divide_seed",
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
        "speedup",
        "variables",
        "clauses"
    ]

def save_curve_row(row_type, experiment, unknown_count, split_positions, divide_trial, divide_seed, branch_id, assignment, branch_order, status, satisfiable, correct, recovered_key, branch_solve_time, experiment_wall_time, baseline_solve_time, variables, clauses):
    file_exists = CURVE_RESULTS_FILE.exists()

    if baseline_solve_time is not None and experiment_wall_time > 0:
        speedup = baseline_solve_time / experiment_wall_time
    else:
        speedup = ""

    with open(CURVE_RESULTS_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(curve_header())

        split_positions_text = ";".join(str(position) for position in split_positions)
        assignment_text = "".join(str(bit) for bit in assignment) if assignment is not None else ""
        recovered_key_hex = "" if recovered_key is None else recovered_key.hex().upper()
        baseline_text = "" if baseline_solve_time is None else baseline_solve_time

        writer.writerow([
            row_type,
            experiment,
            KAT_NAME,
            "last",
            unknown_count,
            128 - unknown_count,
            SPLIT_BITS,
            split_positions_text,
            MAX_WORKERS,
            divide_trial,
            divide_seed,
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
            speedup,
            variables,
            clauses
        ])

def read_curve_rows():
    if not CURVE_RESULTS_FILE.exists():
        return []

    with open(CURVE_RESULTS_FILE, "r", newline="") as file:
        return list(csv.DictReader(file))

def get_experiment_rows(experiment):
    return [row for row in read_curve_rows() if row["experiment"] == experiment]

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

def make_experiment_name(unknown_count, divide_trial):
    return f"{KAT_NAME}_last_{unknown_count}_split{SPLIT_BITS}_divide{divide_trial}_workers{MAX_WORKERS}"

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

def save_checkpoint(experiment, unknown_count, split_positions, divide_trial, divide_seed, total_wall_time, baseline_solve_time, variables, clauses, status):
    save_curve_row(
        "checkpoint",
        experiment,
        unknown_count,
        split_positions,
        divide_trial,
        divide_seed,
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

def finish_summary_from_existing_sat(experiment, unknown_count, split_positions, divide_trial, divide_seed, baseline_solve_time):
    sat_branch = get_experiment_sat_branch(experiment)

    if sat_branch is None:
        return None

    recovered_key_text = sat_branch["recovered_key"]
    recovered_key = bytes.fromhex(recovered_key_text) if recovered_key_text else None
    experiment_wall_time = float(sat_branch["experiment_wall_time"])

    save_curve_row(
        "summary",
        experiment,
        unknown_count,
        split_positions,
        divide_trial,
        divide_seed,
        sat_branch["branch_id"],
        tuple(int(bit) for bit in sat_branch["assignment"]),
        sat_branch["branch_order"],
        "SAT_FOUND",
        True,
        sat_branch["correct"] == "True",
        recovered_key,
        float(sat_branch["branch_solve_time"]),
        experiment_wall_time,
        baseline_solve_time,
        int(sat_branch["variables"]),
        int(sat_branch["clauses"])
    )

    refresh_summary_file()
    return get_experiment_summary(experiment)

def run_divide_experiment(unknown_count, divide_trial):
    experiment = make_experiment_name(unknown_count, divide_trial)
    existing_summary = get_experiment_summary(experiment)

    if existing_summary is not None:
        print()
        print(experiment, "- ALREADY COMPLETED")
        return existing_summary

    case = get_kat_case(KAT_NAME)
    unknown_positions = get_unknown_positions(unknown_count, "last")

    divide_seed, split_positions, assignments = get_divide_plan(
        unknown_positions,
        unknown_count,
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

    baseline_solve_time = get_baseline_last_solve_time(unknown_count)
    completed_branches = get_completed_branches(experiment)
    previous_wall_time = get_previous_wall_time(experiment)

    existing_sat = get_experiment_sat_branch(experiment)

    if existing_sat is not None:
        return finish_summary_from_existing_sat(
            experiment,
            unknown_count,
            split_positions,
            divide_trial,
            divide_seed,
            baseline_solve_time
        )

    pending = []

    for assignment in assignments:
        branch_id = "".join(str(bit) for bit in assignment)

        if branch_id in completed_branches:
            continue

        pending.append(assignment)

    print()
    print("=====================================================")
    print("COUNT1089 LAST DIVIDE CURVE")
    print("Experiment:", experiment)
    print("Unknown bits:", unknown_count)
    print("Known bits:", 128 - unknown_count)
    print("Split bits:", SPLIT_BITS)
    print("Branches:", 2 ** SPLIT_BITS)
    print("Workers:", MAX_WORKERS)
    print("Divide trial:", divide_trial)
    print("Divide seed:", divide_seed)
    print("Split positions:", split_positions)
    print("True branch:", true_branch_id)
    print("True branch order:", assignment_order[true_branch_id], "/", len(assignments))
    print("Completed branches:", len(completed_branches))
    print("Remaining branches:", len(pending))

    if baseline_solve_time is not None:
        print("Single Kissat LAST baseline:", f"{baseline_solve_time:.2f} s")
    else:
        print("Single Kissat LAST baseline: unavailable")

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
        save_curve_row(
            "summary",
            experiment,
            unknown_count,
            split_positions,
            divide_trial,
            divide_seed,
            "",
            None,
            "",
            "UNSAT_ALL",
            False,
            False,
            None,
            0.0,
            previous_wall_time,
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
            while pending and len(active_processes) < MAX_WORKERS:
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
                    experiment,
                    unknown_count,
                    split_positions,
                    divide_trial,
                    divide_seed,
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
                dead_branches = []

                for branch_id, process in active_processes.items():
                    if not process.is_alive():
                        dead_branches.append(branch_id)

                if dead_branches:
                    total_wall_time = previous_wall_time + (perf_counter() - session_start)

                    for branch_id in dead_branches:
                        process = active_processes.pop(branch_id)
                        process.join()
                        assignment = active_assignments.pop(branch_id)

                        print(
                            "Branch",
                            branch_id,
                            "ended without returning a result.",
                            flush=True
                        )

                        pending.insert(0, assignment)

                    save_checkpoint(
                        experiment,
                        unknown_count,
                        split_positions,
                        divide_trial,
                        divide_seed,
                        total_wall_time,
                        baseline_solve_time,
                        instance["variables"],
                        instance["clauses"],
                        "RETRY_DEAD_PROCESS"
                    )

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

            save_curve_row(
                "branch",
                experiment,
                unknown_count,
                split_positions,
                divide_trial,
                divide_seed,
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
                print("Branch error:", result["error"])
                terminate_processes(active_processes)

                save_checkpoint(
                    experiment,
                    unknown_count,
                    split_positions,
                    divide_trial,
                    divide_seed,
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

                save_curve_row(
                    "summary",
                    experiment,
                    unknown_count,
                    split_positions,
                    divide_trial,
                    divide_seed,
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
                    print("Speedup:", f"{baseline_solve_time / total_wall_time:.2f}x")

                return get_experiment_summary(experiment)

        total_wall_time = previous_wall_time + (perf_counter() - session_start)

        save_curve_row(
            "summary",
            experiment,
            unknown_count,
            split_positions,
            divide_trial,
            divide_seed,
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
            experiment,
            unknown_count,
            split_positions,
            divide_trial,
            divide_seed,
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

def refresh_summary_file():
    summaries = []

    for row in read_curve_rows():
        if row["row_type"] == "summary":
            summaries.append(row)

    with open(CURVE_SUMMARY_FILE, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=curve_header())
        writer.writeheader()

        for row in summaries:
            writer.writerow(row)

def get_summary_wall_time(unknown_count, divide_trial):
    experiment = make_experiment_name(unknown_count, divide_trial)
    summary = get_experiment_summary(experiment)

    if summary is None:
        return None

    return float(summary["experiment_wall_time"])

def print_unknown_summary(unknown_count):
    times = []

    for divide_trial in DIVIDE_TRIALS:
        wall_time = get_summary_wall_time(unknown_count, divide_trial)

        if wall_time is not None:
            times.append(wall_time)

    baseline = get_baseline_last_solve_time(unknown_count)

    print()
    print("-----------------------------------------------------")
    print("UNKNOWN BITS SUMMARY:", unknown_count)
    print("Completed divide trials:", len(times), "/", len(DIVIDE_TRIALS))

    if len(times) > 0:
        average = sum(times) / len(times)
        print("Average divide wall time:", f"{average:.2f} s")
        print("Minimum divide wall time:", f"{min(times):.2f} s")
        print("Maximum divide wall time:", f"{max(times):.2f} s")

        if baseline is not None:
            print("Single Kissat LAST baseline:", f"{baseline:.2f} s")
            print("Average speedup:", f"{baseline / average:.2f}x")
        else:
            print("Single Kissat LAST baseline: unavailable")

    print("-----------------------------------------------------")

def print_final_table():
    print()
    print("======================================================================")
    print("FINAL COUNT1089 LAST CURVE")
    print("Unknown | Baseline | Divide avg | Min | Max | Avg speedup")
    print("----------------------------------------------------------------------")

    for unknown_count in UNKNOWN_COUNTS:
        times = []

        for divide_trial in DIVIDE_TRIALS:
            wall_time = get_summary_wall_time(unknown_count, divide_trial)

            if wall_time is not None:
                times.append(wall_time)

        baseline = get_baseline_last_solve_time(unknown_count)

        if len(times) == 0:
            print(unknown_count, "| incomplete")
            continue

        average = sum(times) / len(times)

        if baseline is None:
            print(
                unknown_count,
                "| N/A |",
                f"{average:.2f}s |",
                f"{min(times):.2f}s |",
                f"{max(times):.2f}s | N/A"
            )
        else:
            print(
                unknown_count,
                "|",
                f"{baseline:.2f}s |",
                f"{average:.2f}s |",
                f"{min(times):.2f}s |",
                f"{max(times):.2f}s |",
                f"{baseline / average:.2f}x"
            )

    print("======================================================================")

def run_curve_study():
    print()
    print("=====================================================")
    print("GIFT-COFB COUNT1089 LAST DIVIDE CURVE")
    print("NO TIME LIMIT")
    print("Unknown counts:", UNKNOWN_COUNTS)
    print("Split bits:", SPLIT_BITS)
    print("Workers:", MAX_WORKERS)
    print("Divide trials per point:", len(DIVIDE_TRIALS))
    print("Checkpoint every:", CHECKPOINT_SECONDS, "seconds")
    print("Full results:", CURVE_RESULTS_FILE)
    print("Summary results:", CURVE_SUMMARY_FILE)
    print()
    print("Press Ctrl+C whenever you need to stop.")
    print("Run the same command later to resume.")
    print("=====================================================")

    for unknown_count in UNKNOWN_COUNTS:
        for divide_trial in DIVIDE_TRIALS:
            result = run_divide_experiment(
                unknown_count,
                divide_trial
            )

            if result is None:
                return

        print_unknown_summary(unknown_count)

    refresh_summary_file()
    print_final_table()

    print()
    print("ALL CURVE EXPERIMENTS FINISHED")

def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "run":
        run_curve_study()
        return

    if len(sys.argv) >= 2 and sys.argv[1] == "status":
        refresh_summary_file()
        print_final_table()
        return

    print("Usage:")
    print("python3 -m src.gift_cofb_divide_curve run")
    print("python3 -m src.gift_cofb_divide_curve status")

if __name__ == "__main__":
    main()
