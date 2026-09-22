"""
Generate final tables and figures for the GIFT-COFB SAT analysis.

Run from the repository root:

    python3 analysis/gift_cofb/final_results.py

Inputs:
    analysis/gift_cofb/results/baseline/
    analysis/gift_cofb/results/divide/

Outputs:
    analysis/gift_cofb/figures/
    analysis/gift_cofb/tables/
    analysis/gift_cofb/FINAL_SUMMARY.md
"""

import csv
import statistics
from pathlib import Path
import matplotlib.pyplot as plt

ANALYSIS_DIR = Path(__file__).resolve().parent
BASELINE_DIR = ANALYSIS_DIR / "results" / "baseline"
DIVIDE_DIR = ANALYSIS_DIR / "results" / "divide"
FIGURES_DIR = ANALYSIS_DIR / "figures"
TABLES_DIR = ANALYSIS_DIR / "tables"

LAST_FILE = BASELINE_DIR / "gift_cofb_analysis_results_last.csv"
SOLVERS_FILE = BASELINE_DIR / "gift_cofb_analysis_results_solvers.csv"
UNIQUE_FILE = BASELINE_DIR / "gift_cofb_analysis_results_unique.csv"
CURVE_SUMMARY_FILE = DIVIDE_DIR / "gift_cofb_analysis_results_divide_curve_summary.csv"
NIGHT_SUMMARY_FILE = DIVIDE_DIR / "gift_cofb_analysis_results_divide_night_summary.csv"

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def build_final_curve(last_rows, curve_rows):
    baseline = {}

    for row in last_rows:
        if row["kat"] == "count1089":
            baseline[int(row["unknown_bits"])] = float(row["solve_time"])

    divide = {}

    for row in curve_rows:
        if row["row_type"] != "summary":
            continue

        unknown_bits = int(row["unknown_bits"])
        divide.setdefault(unknown_bits, []).append(float(row["experiment_wall_time"]))

    rows = []

    for unknown_bits in sorted(divide):
        times = divide[unknown_bits]
        average = statistics.mean(times)
        baseline_time = baseline.get(unknown_bits)

        rows.append({
            "unknown_bits": unknown_bits,
            "baseline_solve_time_s": "" if baseline_time is None else baseline_time,
            "divide_avg_wall_time_s": average,
            "divide_min_wall_time_s": min(times),
            "divide_max_wall_time_s": max(times),
            "avg_speedup": "" if baseline_time is None else baseline_time / average,
            "divide_trials": len(times)
        })

    return rows

def build_worker_scaling(night_rows):
    rows = []

    for row in night_rows:
        if row["phase"] != "worker_scaling":
            continue

        baseline = float(row["baseline_solve_time"])
        wall = float(row["experiment_wall_time"])

        rows.append({
            "workers": int(row["max_workers"]),
            "wall_time_s": wall,
            "baseline_solve_time_s": baseline,
            "speedup_vs_single_kissat": baseline / wall
        })

    return sorted(rows, key=lambda row: row["workers"])

def build_split_depth(night_rows):
    times = {}

    for row in night_rows:
        if row["phase"] == "split_depth":
            times.setdefault(int(row["split_bits"]), []).append(float(row["experiment_wall_time"]))

    for row in night_rows:
        if row["phase"] == "worker_scaling" and int(row["max_workers"]) == 8 and int(row["split_bits"]) == 5:
            times.setdefault(5, []).append(float(row["experiment_wall_time"]))

    rows = []

    for split_bits in sorted(times):
        values = times[split_bits]

        rows.append({
            "split_bits": split_bits,
            "branches": 2 ** split_bits,
            "trials": len(values),
            "avg_wall_time_s": statistics.mean(values),
            "min_wall_time_s": min(values),
            "max_wall_time_s": max(values)
        })

    return rows

def save_final_curve_plot(rows):
    x = [row["unknown_bits"] for row in rows]
    divide_avg = [row["divide_avg_wall_time_s"] for row in rows]
    divide_min = [row["divide_min_wall_time_s"] for row in rows]
    divide_max = [row["divide_max_wall_time_s"] for row in rows]
    baseline_rows = [row for row in rows if row["baseline_solve_time_s"] != ""]
    baseline_x = [row["unknown_bits"] for row in baseline_rows]
    baseline_y = [row["baseline_solve_time_s"] for row in baseline_rows]
    lower = [average - minimum for average, minimum in zip(divide_avg, divide_min)]
    upper = [maximum - average for average, maximum in zip(divide_avg, divide_max)]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(baseline_x, baseline_y, marker="o", label="Single Kissat baseline")
    ax.errorbar(x, divide_avg, yerr=[lower, upper], marker="o", capsize=4, label="Divide-and-conquer mean (min–max)")
    ax.set_yscale("log")
    ax.set_xlabel("Unknown key bits")
    ax.set_ylabel("Time [s] — logarithmic scale")
    ax.set_title("GIFT-COFB Count1089 LAST: Single Kissat vs Divide-and-Conquer")
    ax.set_xticks(x)
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "baseline_vs_divide.png", dpi=220)
    plt.close(fig)

def save_speedup_plot(rows):
    comparable = [row for row in rows if row["avg_speedup"] != ""]
    x = [row["unknown_bits"] for row in comparable]
    y = [row["avg_speedup"] for row in comparable]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y, marker="o")
    ax.axhline(1.0, linestyle="--", label="Break-even (1×)")
    ax.set_xlabel("Unknown key bits")
    ax.set_ylabel("Average speedup")
    ax.set_title("Divide-and-Conquer Speedup over Single Kissat")
    ax.set_xticks(x)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "speedup.png", dpi=220)
    plt.close(fig)

def save_worker_plot(rows):
    x = [row["workers"] for row in rows]
    y = [row["wall_time_s"] for row in rows]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, y, marker="o")
    ax.set_xlabel("Maximum parallel workers")
    ax.set_ylabel("Wall time [s]")
    ax.set_title("Worker Scaling — Count1089 RANDOM1, 20 Unknown Bits, Split=5")
    ax.set_xticks(x)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "worker_scaling.png", dpi=220)
    plt.close(fig)

def save_split_plot(rows):
    x = [row["split_bits"] for row in rows]
    average = [row["avg_wall_time_s"] for row in rows]
    minimum = [row["min_wall_time_s"] for row in rows]
    maximum = [row["max_wall_time_s"] for row in rows]
    lower = [avg - mn for avg, mn in zip(average, minimum)]
    upper = [mx - avg for avg, mx in zip(average, maximum)]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.errorbar(x, average, yerr=[lower, upper], marker="o", capsize=4)
    ax.set_xlabel("Split bits")
    ax.set_ylabel("Average wall time [s]")
    ax.set_title("Split-Depth Comparison — Count1089 RANDOM1, 20 Unknown Bits, 8 Workers")
    ax.set_xticks(x)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "split_depth.png", dpi=220)
    plt.close(fig)

def write_final_summary(curve_rows, worker_rows, split_rows):
    by_unknown = {row["unknown_bits"]: row for row in curve_rows}
    row16 = by_unknown[16]
    row18 = by_unknown[18]
    row20 = by_unknown[20]
    row21 = by_unknown[21]
    row24 = by_unknown[24]
    best_split = min(split_rows, key=lambda row: row["avg_wall_time_s"])

    text = f"""# Final GIFT-COFB SAT analysis summary

This file is generated by `analysis/gift_cofb/final_results.py`.

## Headline results

- Final controlled comparison: `Count1089`, `LAST` unknown positions, split depth 5, maximum 8 workers and 3 divide trials per point.
- Around 16 unknown bits the methods are approximately at break-even: `{row16["avg_speedup"]:.2f}x`.
- At 18 unknown bits the average speedup is `{row18["avg_speedup"]:.2f}x`.
- At 20 unknown bits the average speedup is `{row20["avg_speedup"]:.2f}x`.
- At 21 unknown bits the single-Kissat baseline is `{row21["baseline_solve_time_s"]:.2f}s`, while divide-and-conquer averages `{row21["divide_avg_wall_time_s"]:.2f}s`, giving `{row21["avg_speedup"]:.2f}x` average speedup.
- The correct key was also recovered for 22 and 24 unknown LAST bits. No speedup is reported because matching single-Kissat baselines were not measured.
- The 24-bit divide experiments average `{row24["divide_avg_wall_time_s"]:.2f}s` (`{row24["divide_avg_wall_time_s"] / 3600:.2f} h`).

## Tuning results

- Worker scaling reduced wall time from about `{worker_rows[0]["wall_time_s"]:.0f}s` with 1 worker to about `{worker_rows[-1]["wall_time_s"]:.0f}s` with 8 workers.
- Split depth `{best_split["split_bits"]}` had the lowest mean wall time among the tested split depths.
- These tuning experiments motivated the fixed final configuration of 8 workers and split depth 5.

## Methodology caveat

The measured threshold and speedups are empirical for the tested hardware, KAT, unknown-bit placement, Kissat version and divide configuration. They are not universal performance guarantees.

The 22- and 24-bit points are divide-only results and therefore must not be assigned a speedup without a matching baseline.
"""

    (ANALYSIS_DIR / "FINAL_SUMMARY.md").write_text(text, encoding="utf-8")

def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    last_rows = read_csv(LAST_FILE)
    curve_source_rows = read_csv(CURVE_SUMMARY_FILE)
    night_rows = read_csv(NIGHT_SUMMARY_FILE)
    solver_rows = read_csv(SOLVERS_FILE)
    unique_rows = read_csv(UNIQUE_FILE)

    curve_rows = build_final_curve(last_rows, curve_source_rows)
    worker_rows = build_worker_scaling(night_rows)
    split_rows = build_split_depth(night_rows)

    write_csv(TABLES_DIR / "final_curve.csv", list(curve_rows[0].keys()), curve_rows)
    write_csv(TABLES_DIR / "worker_scaling.csv", list(worker_rows[0].keys()), worker_rows)
    write_csv(TABLES_DIR / "split_depth.csv", list(split_rows[0].keys()), split_rows)

    write_csv(
        TABLES_DIR / "solver_comparison.csv",
        ["kat", "solver", "unknown_bits", "solve_time_s", "status", "correct"],
        [{
            "kat": row["kat"],
            "solver": row["solver"],
            "unknown_bits": row["unknown_bits"],
            "solve_time_s": row["solve_time"],
            "status": row["status"],
            "correct": row["correct"]
        } for row in solver_rows]
    )

    write_csv(
        TABLES_DIR / "uniqueness.csv",
        ["case", "kat", "position_mode", "unknown_bits", "solve_time_s", "uniqueness_time_s", "total_time_s", "correct", "unique"],
        [{
            "case": row["case"],
            "kat": row["kat"],
            "position_mode": row["position_mode"],
            "unknown_bits": row["unknown_bits"],
            "solve_time_s": row["solve_time"],
            "uniqueness_time_s": row["uniqueness_time"],
            "total_time_s": row["total_time"],
            "correct": row["correct"],
            "unique": row["unique"]
        } for row in unique_rows]
    )

    save_final_curve_plot(curve_rows)
    save_speedup_plot(curve_rows)
    save_worker_plot(worker_rows)
    save_split_plot(split_rows)
    write_final_summary(curve_rows, worker_rows, split_rows)

    print("Final figures, tables and summary generated successfully.")

if __name__ == "__main__":
    main()
