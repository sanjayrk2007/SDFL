# E12 — Synthetic Leave-One-Client-Out Generalization

> This is **not** true unseen-hospital generalization: repository clients are synthetic, size-biased, overlapping source-record assignments.

## Protocol

Each fold initializes a model from a reproducible random seed; no pretrained checkpoint is loaded. All records assigned to the held-out client are removed from the remaining clients' training and seen-test datasets. Hyperparameters are fixed before running; no held-out-client model selection, threshold tuning, or validation occurs.

| Fold | Train | Held-out | Seen Dice | Held-out Dice | IoU | Precision | Recall | HD95 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A | C0+C1 | C2 | 0.1806 | 0.1759 | 0.1142 | 0.8195 | 0.1230 | 119.26 |
| B | C0+C2 | C1 | 0.1681 | 0.1579 | 0.0988 | 0.8507 | 0.1053 | 126.41 |
| C | C1+C2 | C0 | 0.5784 | 0.3234 | 0.2229 | 0.2557 | 0.7569 | 95.41 |

## Held-out summary

| Statistic | Dice | IoU | Precision | Recall | HD95 |
|---|---:|---:|---:|---:|---:|
| Macro mean | 0.2190 | 0.1453 | 0.6420 | 0.3284 | 113.70 |
| Worst client | 0.1579 | 0.0988 | 0.2557 | 0.1053 | 126.41 |

## Limitation

Record-level exclusion prevents held-out-client training exposure, but cannot make these simulated, overlapping assignments equivalent to independently collected hospital cohorts.
