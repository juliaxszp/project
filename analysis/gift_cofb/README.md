# GIFT-COFB SAT analysis

This file explains where the analysis CSV files came from and which results are used for the final conclusions. The analysis is stored under `analysis/gift_cofb/`. Baseline CSV files live in `results/baseline/`, divide-and-conquer CSV files in `results/divide/`, and final figures/tables are generated into `figures/` and `tables/`.

## Source code

### `src/gift_cofb_analysis.py`

Reusable SAT-analysis core: KAT definitions, SAT bit conversion, partially unknown keys, CNF construction, Kissat key recovery, uniqueness helper functions and deterministic FIRST/LAST/RANDOM key-position selection.

Smoke test:

```bash
python3 -m src.gift_cofb_analysis smoke
```

### `src/gift_cofb_divide_curve.py`

Final resumable divide-and-conquer runner. It compares the same `Count1089` / `LAST` family against the earlier single-Kissat baseline while changing only the number of unknown key bits.

Final configuration:

- `Count1089`
- `LAST` unknown positions
- unknown bits: `8, 10, 12, 14, 16, 18, 20, 21, 22, 24`
- `split_bits = 5` -> 32 branches
- `max_workers = 8`
- 3 randomized divide trials per point

Run:

```bash
caffeinate -i python3 -m src.gift_cofb_divide_curve run
```

The command can be stopped with `Ctrl+C` and resumed with the same command.

## Directory layout

```text
analysis/gift_cofb/
├── README.md
├── results/
│   ├── baseline/
│   └── divide/
├── figures/
└── tables/
```

## Result-file provenance

### Baseline results (`results/baseline/`)

#### `gift_cofb_analysis_results_last.csv`

Single-Kissat progressive LAST baseline. This is the main baseline used by the final divide curve.

#### `gift_cofb_analysis_results_first.csv`

FIRST-position study for selected unknown-bit counts.

#### `gift_cofb_analysis_results_random.csv`

RANDOM-position study. Each random selection is reproducible because its seed and exact unknown positions are stored in the CSV.

#### `gift_cofb_analysis_results_unique.csv`

Uniqueness verification. After a key is recovered, its full assignment is blocked and a second SAT solve is performed. If the second problem is UNSAT, the recovered key is unique for that experiment.

#### `gift_cofb_analysis_results_solvers.csv`

Solver comparison. The file contains completed solves and explicit TIMEOUT rows. A timeout is not interpreted as UNSAT.

### Divide-and-conquer results (`results/divide/`)

#### `gift_cofb_analysis_results_divide.csv`

Initial divide-and-conquer pilot. It tested split depths 2-5. This experiment revealed a favourable branch-order bias and is retained as historical development data, not as the main final benchmark.

#### `gift_cofb_analysis_results_divide_randomized.csv`

Follow-up divide experiment with randomized split positions and branch scheduling, plus worker-count tests. This removed the favourable ordering bias from the pilot.

#### `gift_cofb_analysis_results_divide_night.csv`

Raw data from the larger tuning study.

#### `gift_cofb_analysis_results_divide_night_summary.csv`

Summary of worker scaling, split-depth comparison, generalization to other random 20-bit instances and the 22-bit challenge. These experiments motivated the final choice of 8 workers and split depth 5.

#### `gift_cofb_analysis_results_divide_curve.csv`

Raw branch/checkpoint data from the final Count1089 LAST curve.

#### `gift_cofb_analysis_results_divide_curve_summary.csv`

Final per-trial summaries. This is the primary divide-and-conquer file for final plots and conclusions.

## Important columns

- `unknown_bits` - key bits intentionally left unconstrained.
- `known_bits` - `128 - unknown_bits`.
- `solve_time` / `branch_solve_time` - time used by one solver invocation.
- `experiment_wall_time` - real elapsed time until the complete parallel experiment found SAT.
- `baseline_solve_time` - matching single-Kissat reference when available.
- `speedup` - `baseline_solve_time / experiment_wall_time`.
- `split_bits` - number of unknown key bits fixed to define divide branches.
- `branch_order` - randomized scheduling position of a branch.
- `max_workers` - maximum number of simultaneous Kissat processes.
- `correct=True` - recovered model matches the KAT key.

## Methodology notes

The KAT key is known because these are controlled experiments. Only bits declared as known are constrained in the SAT instance; unknown positions remain free. The known key is also used after solving to verify correctness. Diagnostic output such as `true branch` is not used to schedule the branch order.

For small SAT instances the divide approach can be slower because process startup, branch scheduling and repeated UNSAT proofs add overhead. As the instance becomes harder, parallel branch solving becomes beneficial. The final curve is designed to show this transition under one fixed experimental configuration.

No speedup should be claimed for 22 or 24 unknown LAST bits unless a matching single-Kissat baseline is actually measured.

## Files to use for the final report

Use primarily:

- `gift_cofb_analysis_results_last.csv`
- `gift_cofb_analysis_results_first.csv`
- `gift_cofb_analysis_results_random.csv`
- `gift_cofb_analysis_results_unique.csv`
- `gift_cofb_analysis_results_solvers.csv`
- `gift_cofb_analysis_results_divide_night_summary.csv`
- `gift_cofb_analysis_results_divide_curve_summary.csv`

Keep the raw divide CSV files in the repository as provenance/debug data, but use the summary files for figures and tables.
