# DyBenchEval

This repository contains the curated code for the DyBenchEval experiments. It is organized as a seven-stage pipeline and uses English-only directory and file names.

The repository intentionally contains code only. Dataset files, model generations, annotations, scores, checkpoints, and other large artifacts remain local and are ignored by Git. The dataset will be supplied separately.

## Repository scope

- 194 Python scripts are included: the selected experiment pipeline, dataset extractors, `config.py`, and the migration helper.
- All 194 Python files pass AST parsing and contain no syntax errors.
- The original workspace contains 740 Python files. The curated set therefore represents a selected subset, not every historical or third-party file.
- The local `data/` directory contains 117 JSONL snapshots (about 487 MB) for reference only and is excluded from the Git commit.

## Pipeline

```text
01_data_preparation
    -> 02_data_augmentation
    -> 03_main_experiments
    -> 04_evaluation_metrics
    -> 05_human_evaluation
    -> 06_ablation_and_significance
    -> 07_results_and_tables
```

Each stage contains standalone scripts rather than an importable package. Most scripts are intended to be run directly after their input files and environment variables have been prepared.

## Setup

```bash
python -m pip install -r requirements.txt

# Original project/data tree; change this on another machine.
export DYBENCH_ROOT="/path/to/project1"
export DYBENCH_RAW="/path/to/project1/all_datasets"

# Required only for scripts that call an external model API.
export DYBENCH_API_KEY="<your-api-key>"
export DYBENCH_API_BASE="https://api.whatai.cc/v1"

python config.py
```

`config.py` exposes `PROJECT_ROOT`, `DATA_ROOT`, `ORIG_ROOT`, `RAW_DATASETS`, `API_BASE`, and `API_KEY` for scripts that choose to use the shared configuration.

## Important limitations found during review

1. Many legacy scripts still contain hard-coded paths into the original experiment tree. They are preserved for reproducibility, but they are not portable until those paths are converted to `config.py` or environment-based paths.
2. The scripts are mostly independent command-line entry points, so static import analysis cannot prove that every file is executed by the final tables. The active final-results chain is the rewrite prompt generation, model API calls, provenance labeling, coherence/correctness/diversity scoring, aggregation, and table generation. Dataset extractors and scripts in `misc/` are auxiliary or one-off utilities.
3. Some historical scripts are intentionally retained for traceability and are marked `legacy`, `misc`, or `remaining` in their names or directories.
4. No API key is committed. Before running API scripts, set `DYBENCH_API_KEY` in the environment.

## Data policy

The local `data/` tree is ignored and must not be committed. To reproduce the experiments, place the supplied dataset under the location configured by `DYBENCH_RAW`, then run the relevant scripts in `01_data_preparation/`.

## Traceability

`file_mapping.md` records the relationship between the curated scripts and their original source locations. `migration.py` is retained as a historical migration tool; it is not required for normal experiment execution.
