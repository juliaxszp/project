"""
Byte-position SAT study for GIFT-128.

Run from repository root:
    python3 analysis/gift_cofb/byte_position_analysis.py pilot
    python3 analysis/gift_cofb/byte_position_analysis.py single 10
    python3 analysis/gift_cofb/byte_position_analysis.py pairs 1
    python3 analysis/gift_cofb/byte_position_analysis.py plots
    python3 analysis/gift_cofb/byte_position_analysis.py status
"""

import csv
import math
import random
import statistics
import sys
from itertools import combinations
from multiprocessing import get_context
from pathlib import Path
from queue import Empty
from time import perf_counter

PROJECT_DIR = Path(__file__).resolve().parents[2]

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import matplotlib.pyplot as plt
from pysat.solvers import Kissat404
from src.basics import BasicFunctions
from src.gift_cofb import cofb_gift_encrypt
from src.gift_cofb_analysis import bytes_to_fixed_sat_bits, constrain_sat_bits_to_bytes, key_to_sat_bits_with_unknowns, sat_bits_to_bytes
from src.gift_cofb_reference import gift128_reference

ANALYSIS_DIR = Path(__file__).resolve().parent
RESULTS_DIR = ANALYSIS_DIR / "results" / "byte_positions"
FIGURES_DIR = ANALYSIS_DIR / "figures" / "byte_positions"
TABLES_DIR = ANALYSIS_DIR / "tables" / "byte_positions"

PILOT_RESULTS_FILE = RESULTS_DIR / "pilot_scaling.csv"
SINGLE_RESULTS_FILE = RESULTS_DIR / "single_bytes.csv"
PAIR_RESULTS_FILE = RESULTS_DIR / "byte_pairs.csv"

PILOT_SUMMARY_FILE = TABLES_DIR / "pilot_scaling_summary.csv"
SINGLE_SUMMARY_FILE = TABLES_DIR / "single_bytes_summary.csv"
PAIR_SUMMARY_FILE = TABLES_DIR / "byte_pairs_summary.csv"

INSTANCE_SEED_BASE = 2026092200
PILOT_SELECTION_SEED_BASE = 2026092300

PILOT_UNKNOWN_BYTE_COUNTS = [1, 2, 3]
PILOT_TRIALS = 5
PILOT_TIMEOUT_SECONDS = 120

SINGLE_DEFAULT_TRIALS = 10
SINGLE_TIMEOUT_SECONDS = 60

PAIR_DEFAULT_TRIALS = 1
PAIR_TIMEOUT_SECONDS = 120

def ensure_directories():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

def unknown_bytes_to_bit_positions(unknown_bytes):
    positions = []

    for byte_index in unknown_bytes:
        start = byte_index * 8

        for bit_offset in range(8):
            positions.append(start + bit_offset)

    return positions

def make_trial_instance(trial):
    seed = INSTANCE_SEED_BASE + trial
    rng = random.Random(seed)

    plaintext = bytes(rng.randrange(256) for _ in range(16))
    key = bytes(rng.randrange(256) for _ in range(16))
    ciphertext = bytes(gift128_reference(plaintext, key))

    return {
        "trial": trial,
        "seed": seed,
        "plaintext": plaintext,
        "key": key,
        "ciphertext": ciphertext
    }

def build_recovery_instance(plaintext, key, ciphertext, unknown_bytes):
    build_start = perf_counter()
    builder = BasicFunctions()

    unknown_positions = unknown_bytes_to_bit_positions(unknown_bytes)

    plaintext_bits = bytes_to_fixed_sat_bits(builder, plaintext, "byte_study_plaintext")
    key_bits = key_to_sat_bits_with_unknowns(builder, key, unknown_positions, "byte_study_key")
    ciphertext_bits = cofb_gift_encrypt(builder, plaintext_bits, key_bits, "byte_study_gift")

    constrain_sat_bits_to_bytes(builder, ciphertext_bits, ciphertext)

    return {
        "builder": builder,
        "key_bits": key_bits,
        "build_time": perf_counter() - build_start,
        "variables": builder.idp.top,
        "clauses": len(builder.cnf.clauses)
    }

def solve_case_worker(plaintext, key, ciphertext, unknown_bytes, result_queue):
    total_start = perf_counter()

    try:
        instance = build_recovery_instance(plaintext, key, ciphertext, unknown_bytes)
        solve_start = perf_counter()

        with Kissat404(bootstrap_with=instance["builder"].cnf.clauses) as solver:
            satisfiable = solver.solve()
            model = solver.get_model() if satisfiable else None

        solve_time = perf_counter() - solve_start

        if satisfiable:
            recovered_key = sat_bits_to_bytes(instance["key_bits"], model)
            recovered_ciphertext = bytes(gift128_reference(plaintext, recovered_key))
            correct = recovered_key == key
            candidate_valid = recovered_ciphertext == ciphertext
        else:
            recovered_key = None
            correct = False
            candidate_valid = False

        result_queue.put({
            "status": "SAT" if satisfiable else "UNSAT",
            "satisfiable": satisfiable,
            "correct": correct,
            "candidate_valid": candidate_valid,
            "recovered_key": recovered_key,
            "build_time": instance["build_time"],
            "solve_time": solve_time,
            "total_time": perf_counter() - total_start,
            "variables": instance["variables"],
            "clauses": instance["clauses"],
            "error": ""
        })

    except Exception as error:
        result_queue.put({
            "status": "ERROR",
            "satisfiable": False,
            "correct": False,
            "candidate_valid": False,
            "recovered_key": None,
            "build_time": 0.0,
            "solve_time": 0.0,
            "total_time": perf_counter() - total_start,
            "variables": 0,
            "clauses": 0,
            "error": str(error)
        })

def solve_case_with_timeout(plaintext, key, ciphertext, unknown_bytes, timeout_seconds):
    context = get_context("fork")
    result_queue = context.Queue()
    process = context.Process(target=solve_case_worker, args=(plaintext, key, ciphertext, unknown_bytes, result_queue))
    process.start()

    try:
        result = result_queue.get(timeout=timeout_seconds)
        process.join()
        return result

    except Empty:
        if process.is_alive():
            process.terminate()

        process.join()

        return {
            "status": "TIMEOUT",
            "satisfiable": False,
            "correct": False,
            "candidate_valid": False,
            "recovered_key": None,
            "build_time": "",
            "solve_time": "",
            "total_time": timeout_seconds,
            "variables": "",
            "clauses": "",
            "error": f"Exceeded timeout of {timeout_seconds} seconds"
        }

def result_header():
    return [
        "study",
        "trial",
        "seed",
        "unknown_byte_count",
        "unknown_bytes",
        "unknown_bits",
        "plaintext",
        "key",
        "ciphertext",
        "status",
        "satisfiable",
        "correct",
        "candidate_valid",
        "recovered_key",
        "build_time",
        "solve_time",
        "total_time",
        "timeout_seconds",
        "variables",
        "clauses",
        "error"
    ]

def append_result(path, study, instance, unknown_bytes, timeout_seconds, result):
    file_exists = path.exists()

    with open(path, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=result_header())

        if not file_exists:
            writer.writeheader()

        recovered_key = result["recovered_key"]

        writer.writerow({
            "study": study,
            "trial": instance["trial"],
            "seed": instance["seed"],
            "unknown_byte_count": len(unknown_bytes),
            "unknown_bytes": ";".join(str(value) for value in unknown_bytes),
            "unknown_bits": len(unknown_bytes) * 8,
            "plaintext": instance["plaintext"].hex().upper(),
            "key": instance["key"].hex().upper(),
            "ciphertext": instance["ciphertext"].hex().upper(),
            "status": result["status"],
            "satisfiable": result["satisfiable"],
            "correct": result["correct"],
            "candidate_valid": result["candidate_valid"],
            "recovered_key": "" if recovered_key is None else recovered_key.hex().upper(),
            "build_time": result["build_time"],
            "solve_time": result["solve_time"],
            "total_time": result["total_time"],
            "timeout_seconds": timeout_seconds,
            "variables": result["variables"],
            "clauses": result["clauses"],
            "error": result["error"]
        })

def read_rows(path):
    if not path.exists():
        return []

    with open(path, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

def case_exists(path, trial, unknown_bytes):
    target = ";".join(str(value) for value in unknown_bytes)

    for row in read_rows(path):
        if int(row["trial"]) == trial and row["unknown_bytes"] == target:
            return True

    return False

def run_one_case(path, study, trial, unknown_bytes, timeout_seconds):
    if case_exists(path, trial, unknown_bytes):
        print("SKIP", study, "| trial", trial, "| unknown bytes", unknown_bytes)
        return

    instance = make_trial_instance(trial)

    print(
        "RUN",
        study,
        "| trial",
        trial,
        "| seed",
        instance["seed"],
        "| unknown bytes",
        unknown_bytes,
        "| unknown bits",
        len(unknown_bytes) * 8,
        flush=True
    )

    result = solve_case_with_timeout(
        instance["plaintext"],
        instance["key"],
        instance["ciphertext"],
        unknown_bytes,
        timeout_seconds
    )

    append_result(path, study, instance, unknown_bytes, timeout_seconds, result)

    print(
        "  ->",
        result["status"],
        "| solve:",
        "-" if result["solve_time"] == "" else f'{float(result["solve_time"]):.4f}s',
        "| total:",
        f'{float(result["total_time"]):.4f}s',
        "| correct:",
        result["correct"],
        "| valid candidate:",
        result["candidate_valid"],
        flush=True
    )

def pilot_unknown_bytes(trial, unknown_byte_count):
    seed = PILOT_SELECTION_SEED_BASE + trial * 100 + unknown_byte_count
    rng = random.Random(seed)

    return sorted(rng.sample(range(16), unknown_byte_count))

def run_pilot():
    ensure_directories()

    print()
    print("============================================================")
    print("GIFT-128 BYTE SCALING PILOT")
    print("Trials:", PILOT_TRIALS)
    print("Unknown byte counts:", PILOT_UNKNOWN_BYTE_COUNTS)
    print("Timeout per case:", PILOT_TIMEOUT_SECONDS, "seconds")
    print("============================================================")
    print()

    for trial in range(1, PILOT_TRIALS + 1):
        for unknown_byte_count in PILOT_UNKNOWN_BYTE_COUNTS:
            unknown_bytes = pilot_unknown_bytes(trial, unknown_byte_count)
            run_one_case(PILOT_RESULTS_FILE, "pilot", trial, unknown_bytes, PILOT_TIMEOUT_SECONDS)

    generate_all_outputs()

def run_single(trials):
    ensure_directories()

    print()
    print("============================================================")
    print("GIFT-128 SINGLE UNKNOWN BYTE POSITION STUDY")
    print("Trials per byte:", trials)
    print("Total planned cases:", trials * 16)
    print("Timeout per case:", SINGLE_TIMEOUT_SECONDS, "seconds")
    print("============================================================")
    print()

    for trial in range(1, trials + 1):
        for byte_index in range(16):
            run_one_case(SINGLE_RESULTS_FILE, "single", trial, [byte_index], SINGLE_TIMEOUT_SECONDS)

    generate_all_outputs()

def run_pairs(trials):
    ensure_directories()
    all_pairs = list(combinations(range(16), 2))

    print()
    print("============================================================")
    print("GIFT-128 UNKNOWN BYTE-PAIR POSITION STUDY")
    print("Trials per pair:", trials)
    print("Pairs:", len(all_pairs))
    print("Total planned cases:", trials * len(all_pairs))
    print("Timeout per case:", PAIR_TIMEOUT_SECONDS, "seconds")
    print("============================================================")
    print()

    for trial in range(1, trials + 1):
        for first, second in all_pairs:
            run_one_case(PAIR_RESULTS_FILE, "pairs", trial, [first, second], PAIR_TIMEOUT_SECONDS)

    generate_all_outputs()

def successful_solve_times(rows):
    return [
        float(row["solve_time"])
        for row in rows
        if row["status"] == "SAT" and row["solve_time"] != ""
    ]

def calculate_stats(rows):
    times = successful_solve_times(rows)
    sat_count = sum(1 for row in rows if row["status"] == "SAT")
    timeout_count = sum(1 for row in rows if row["status"] == "TIMEOUT")
    error_count = sum(1 for row in rows if row["status"] == "ERROR")
    correct_count = sum(1 for row in rows if row["correct"] == "True")
    candidate_valid_count = sum(1 for row in rows if row["candidate_valid"] == "True")

    if len(times) == 0:
        return {
            "cases": len(rows),
            "sat": sat_count,
            "timeouts": timeout_count,
            "errors": error_count,
            "correct": correct_count,
            "candidate_valid": candidate_valid_count,
            "mean": "",
            "median": "",
            "min": "",
            "max": "",
            "stdev": ""
        }

    stdev = statistics.stdev(times) if len(times) >= 2 else 0.0

    return {
        "cases": len(rows),
        "sat": sat_count,
        "timeouts": timeout_count,
        "errors": error_count,
        "correct": correct_count,
        "candidate_valid": candidate_valid_count,
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "stdev": stdev
    }

def write_pilot_summary():
    rows = read_rows(PILOT_RESULTS_FILE)

    if len(rows) == 0:
        return []

    summary = []

    for unknown_byte_count in PILOT_UNKNOWN_BYTE_COUNTS:
        selected = [row for row in rows if int(row["unknown_byte_count"]) == unknown_byte_count]

        if len(selected) == 0:
            continue

        summary.append({
            "unknown_byte_count": unknown_byte_count,
            "unknown_bits": unknown_byte_count * 8,
            **calculate_stats(selected)
        })

    fieldnames = [
        "unknown_byte_count",
        "unknown_bits",
        "cases",
        "sat",
        "timeouts",
        "errors",
        "correct",
        "candidate_valid",
        "mean",
        "median",
        "min",
        "max",
        "stdev"
    ]

    with open(PILOT_SUMMARY_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)

    return summary

def write_single_summary():
    rows = read_rows(SINGLE_RESULTS_FILE)

    if len(rows) == 0:
        return []

    summary = []

    for byte_index in range(16):
        selected = [row for row in rows if row["unknown_bytes"] == str(byte_index)]

        if len(selected) == 0:
            continue

        summary.append({
            "byte_index": byte_index,
            **calculate_stats(selected)
        })

    fieldnames = [
        "byte_index",
        "cases",
        "sat",
        "timeouts",
        "errors",
        "correct",
        "candidate_valid",
        "mean",
        "median",
        "min",
        "max",
        "stdev"
    ]

    with open(SINGLE_SUMMARY_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)

    return summary

def write_pair_summary():
    rows = read_rows(PAIR_RESULTS_FILE)

    if len(rows) == 0:
        return []

    summary = []

    for first, second in combinations(range(16), 2):
        label = f"{first};{second}"
        selected = [row for row in rows if row["unknown_bytes"] == label]

        if len(selected) == 0:
            continue

        summary.append({
            "byte_a": first,
            "byte_b": second,
            **calculate_stats(selected)
        })

    fieldnames = [
        "byte_a",
        "byte_b",
        "cases",
        "sat",
        "timeouts",
        "errors",
        "correct",
        "candidate_valid",
        "mean",
        "median",
        "min",
        "max",
        "stdev"
    ]

    with open(PAIR_SUMMARY_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary)

    return summary

def plot_pilot(summary):
    usable = [row for row in summary if row["median"] != ""]

    if len(usable) == 0:
        return

    x = [row["unknown_bits"] for row in usable]
    mean = [row["mean"] for row in usable]
    median = [row["median"] for row in usable]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(x, mean, marker="o", label="Mean solve time")
    ax.plot(x, median, marker="o", label="Median solve time")
    ax.set_xlabel("Unknown key bits")
    ax.set_ylabel("Solve time [s]")
    ax.set_title("GIFT-128 SAT Scaling by Number of Unknown Key Bytes")
    ax.set_xticks(x)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "byte_scaling.png", dpi=220)
    plt.close(fig)

def plot_single(summary):
    usable = [row for row in summary if row["mean"] != ""]

    if len(usable) == 0:
        return

    x = [row["byte_index"] for row in usable]
    mean = [row["mean"] for row in usable]
    minimum = [row["min"] for row in usable]
    maximum = [row["max"] for row in usable]
    lower = [avg - mn for avg, mn in zip(mean, minimum)]
    upper = [mx - avg for avg, mx in zip(mean, maximum)]

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.errorbar(x, mean, yerr=[lower, upper], marker="o", capsize=4)
    ax.set_xlabel("Unknown key-byte position")
    ax.set_ylabel("Mean solve time [s]")
    ax.set_title("GIFT-128 SAT Difficulty by Single Unknown Key Byte")
    ax.set_xticks(range(16))
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "single_byte_positions.png", dpi=220)
    plt.close(fig)

def plot_pairs(summary):
    if len(summary) == 0:
        return

    matrix = [[math.nan for _ in range(16)] for _ in range(16)]
    timeout_matrix = [[math.nan for _ in range(16)] for _ in range(16)]
    any_timeouts = False

    for row in summary:
        first = int(row["byte_a"])
        second = int(row["byte_b"])

        if row["median"] != "":
            value = float(row["median"])
            matrix[first][second] = value
            matrix[second][first] = value

        cases = int(row["cases"])
        timeouts = int(row["timeouts"])

        if cases > 0:
            timeout_rate = 100.0 * timeouts / cases
            timeout_matrix[first][second] = timeout_rate
            timeout_matrix[second][first] = timeout_rate

            if timeouts > 0:
                any_timeouts = True

    fig, ax = plt.subplots(figsize=(9, 8))
    image = ax.imshow(matrix)
    ax.set_xlabel("Key byte B")
    ax.set_ylabel("Key byte A")
    ax.set_title("Median SAT Solve Time for Unknown Key-Byte Pairs")
    ax.set_xticks(range(16))
    ax.set_yticks(range(16))
    fig.colorbar(image, ax=ax, label="Median solve time [s]")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "byte_pair_heatmap.png", dpi=220)
    plt.close(fig)

    if any_timeouts:
        fig, ax = plt.subplots(figsize=(9, 8))
        image = ax.imshow(timeout_matrix)
        ax.set_xlabel("Key byte B")
        ax.set_ylabel("Key byte A")
        ax.set_title("Timeout Rate for Unknown Key-Byte Pairs")
        ax.set_xticks(range(16))
        ax.set_yticks(range(16))
        fig.colorbar(image, ax=ax, label="Timeout rate [%]")
        fig.tight_layout()
        fig.savefig(FIGURES_DIR / "byte_pair_timeout_heatmap.png", dpi=220)
        plt.close(fig)

def print_top_single(summary):
    usable = [row for row in summary if row["median"] != ""]

    if len(usable) == 0:
        return

    ordered = sorted(usable, key=lambda row: float(row["median"]))

    print()
    print("SINGLE-BYTE POSITION SUMMARY")
    print("----------------------------")
    print("Fastest by median:")

    for row in ordered[:3]:
        print(" byte", row["byte_index"], "| median", f'{float(row["median"]):.4f}s', "| mean", f'{float(row["mean"]):.4f}s')

    print("Slowest by median:")

    for row in ordered[-3:]:
        print(" byte", row["byte_index"], "| median", f'{float(row["median"]):.4f}s', "| mean", f'{float(row["mean"]):.4f}s')

def print_top_pairs(summary):
    usable = [row for row in summary if row["median"] != ""]

    if len(usable) == 0:
        return

    ordered = sorted(usable, key=lambda row: float(row["median"]))

    print()
    print("BYTE-PAIR POSITION SUMMARY")
    print("--------------------------")
    print("Fastest by median:")

    for row in ordered[:5]:
        print(f' bytes {row["byte_a"]},{row["byte_b"]}', "| median", f'{float(row["median"]):.4f}s', "| mean", f'{float(row["mean"]):.4f}s')

    print("Slowest by median:")

    for row in ordered[-5:]:
        print(f' bytes {row["byte_a"]},{row["byte_b"]}', "| median", f'{float(row["median"]):.4f}s', "| mean", f'{float(row["mean"]):.4f}s')

def generate_all_outputs():
    ensure_directories()

    pilot_summary = write_pilot_summary()
    single_summary = write_single_summary()
    pair_summary = write_pair_summary()

    plot_pilot(pilot_summary)
    plot_single(single_summary)
    plot_pairs(pair_summary)

    print_top_single(single_summary)
    print_top_pairs(pair_summary)

def print_file_status(name, path):
    rows = read_rows(path)
    sat = sum(1 for row in rows if row["status"] == "SAT")
    timeouts = sum(1 for row in rows if row["status"] == "TIMEOUT")
    errors = sum(1 for row in rows if row["status"] == "ERROR")

    print(name, "| rows:", len(rows), "| SAT:", sat, "| TIMEOUT:", timeouts, "| ERROR:", errors)

def print_status():
    ensure_directories()

    print()
    print("GIFT-128 BYTE POSITION ANALYSIS STATUS")
    print("======================================")
    print_file_status("Pilot ", PILOT_RESULTS_FILE)
    print_file_status("Single", SINGLE_RESULTS_FILE)
    print_file_status("Pairs ", PAIR_RESULTS_FILE)
    print()
    print("Results directory:", RESULTS_DIR)
    print("Figures directory:", FIGURES_DIR)
    print("Tables directory:", TABLES_DIR)

def print_usage():
    print()
    print("Usage:")
    print("python3 analysis/gift_cofb/byte_position_analysis.py pilot")
    print("python3 analysis/gift_cofb/byte_position_analysis.py single [trials]")
    print("python3 analysis/gift_cofb/byte_position_analysis.py pairs [trials]")
    print("python3 analysis/gift_cofb/byte_position_analysis.py plots")
    print("python3 analysis/gift_cofb/byte_position_analysis.py status")
    print()
    print("Recommended sequence:")
    print("1. pilot")
    print("2. single 10")
    print("3. pairs 1")
    print("4. inspect timing")
    print("5. pairs 5 only if runtime is acceptable")

def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1]

    if command == "pilot":
        run_pilot()
        return

    if command == "single":
        trials = int(sys.argv[2]) if len(sys.argv) >= 3 else SINGLE_DEFAULT_TRIALS
        run_single(trials)
        return

    if command == "pairs":
        trials = int(sys.argv[2]) if len(sys.argv) >= 3 else PAIR_DEFAULT_TRIALS
        run_pairs(trials)
        return

    if command == "plots":
        generate_all_outputs()
        return

    if command == "status":
        print_status()
        return

    print("Unknown command:", command)
    print_usage()

if __name__ == "__main__":
    main()
