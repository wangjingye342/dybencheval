# Curated file mapping

The curated tree is a renamed copy of selected scripts from the original
`project1` workspace. The directory names in this repository are English;
historical source paths are kept only as provenance in the original migration
notes and are not required to run the code.

## Stage mapping

| Repository directory | Original role |
|---|---|
| `01_data_preparation/` | Dataset extraction, assembly, sampling, and statistics. |
| `02_data_augmentation/` | Prompt construction, generation, cleaning, and embeddings. |
| `03_main_experiments/` | Rewrite prompt generation and model API calls. |
| `04_evaluation_metrics/` | Provenance, coherence, correctness, and diversity metrics. |
| `05_human_evaluation/` | Human labels, agreement analysis, ranking, and model re-evaluation. |
| `06_ablation_and_significance/` | Prompt variants, ablation scoring, and significance tests. |
| `07_results_and_tables/` | Aggregation, tables, and similarity heatmaps. |

The historical migration helper is retained as `migration.py` for auditability.
It is not part of the normal experiment execution path.

