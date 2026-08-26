# Code usage and curation review

## Inventory

| Scope | Count | Interpretation |
|---|---:|---|
| Original workspace Python files | 740 | Includes historical scripts, backups, and third-party baseline copies from the wider workspace. |
| Curated Python files | 193 | The seven-stage experiment pipeline, dataset extractors, and `config.py`. |
| Curated JSONL snapshots | 117 | Local data only; excluded from Git. |

The curated tree is therefore not intended to contain every historical file. It is a selected, reproducibility-oriented subset. The omitted files are predominantly third-party baselines, backup copies, temporary patches, duplicate scripts, and old result-processing utilities.

## Are all curated scripts used?

Not in the sense of being imported by one central program. The scripts are standalone entry points. Static import analysis shows that they are mostly not imported by each other; they are run manually in pipeline order.

The final-results chain identified from the scripts and produced artifacts is:

```text
build rewrite prompts
  -> call model APIs
  -> add provenance labels
  -> score coherence, correctness, and diversity
  -> aggregate results
  -> generate tables and heatmaps
```

The following groups are active or directly supporting that chain:

- `03_main_experiments/`: prompt construction and model API calls.
- `04_evaluation_metrics/`: provenance, judge prompts, score extraction, and diversity metrics.
- `07_results_and_tables/`: aggregation and final tables.
- The relevant parts of `01_data_preparation/`, `02_data_augmentation/`, `05_human_evaluation/`, and `06_ablation_and_significance/` support dataset construction, augmentation, human validation, and ablation experiments.

The following groups are auxiliary rather than guaranteed to run in every final experiment:

- Dataset-specific extractors under `01_data_preparation/extraction_scripts/`.
- Files under `misc/`.
- Files with `legacy`, `remaining`, or one-off sampling/diagnostic names.
- Historical migration metadata, which was removed because it contained machine-specific source paths.

That means the answer to “are all these scripts used?” is **no for the final run**, but **yes for the curated scope**: every retained file has a documented role, source mapping, or traceability purpose. Some are optional utilities and are not on the main execution path.

## Problems found

1. All 193 Python files parse successfully. The machine-specific absolute paths found during the first review have been removed. Required external inputs now use relative paths under generic `./external` or `./data` prefixes, while nonessential historical path metadata was deleted.
2. The previous README claimed that no absolute paths remained; the repository now enforces that claim with a final path scan.
3. The old workspace has no single package entry point or automated pipeline runner. Reproducing the paper results requires running scripts manually with the expected intermediate files.
4. Several historical scripts use filenames and working-directory assumptions rather than explicit command-line arguments. Run them from the directory expected by the script, or refactor them to accept paths.
5. API scripts depend on external services and environment variables. No API key was found in the curated source, but network/model availability is not guaranteed.
