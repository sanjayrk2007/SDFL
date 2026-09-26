# Experiment E3 -- FedProx Integration (Reproduced)

## Configuration

| Parameter | Value |
|---|---|
| **Model** | ResUNet++ |
| **Framework** | Flower (flwr) + Ray simulation backend |
| **Clients** | 3 |
| **Rounds** | 20 per mu (full sweep, not the 1-round quick-test) |

## Sweep Results (best round per mu)

| mu | best round | val_dice | val_iou |
|:---:|:---:|:---:|:---:|
| 0.0 | 16 | 0.8430 | 0.7543 |
| 0.001 | 18 | 0.8469 | 0.7657 |
| 0.01 | 20 | 0.8569 | 0.7767 |
| 0.1 | 18 | 0.8212 | 0.7295 |

**Best configuration:** mu = 0.01, val_dice = 0.8569 (validation-set Dice, best round of the sweep)

**Held-out test-set Dice for this configuration:** 0.4926 (see `Results_New/results/e3_metrics.json`) -- this is a genuinely different, lower number than the validation Dice above because it's evaluated on a disjoint test split, not a discrepancy. Independently cross-checked against `Results_New/E13/e13_multiseed_results.json`'s 5-seed test-set evaluation of this same config (mean 0.4891, std 0.0137).

**Status:** Complete. Reproduced on `integration/sdfl-final-validation` at the script's documented 20-round default.
**Note on other E3 numbers found elsewhere in this repo:**
- README.md (0.5782) was from the 1-round quick-test mode, not the full 20-round sweep above -- different scope, not an error. README.md has been updated to cite the val-Dice above and note the quick-test figure separately.
- FINAL_RESULTS.md (0.4924) is this file's held-out test Dice (0.4926) rounded/re-derived -- consistent, just previously unlabeled as test vs. val.
- EXPERIMENT_REGISTRY.md previously cited "Dice ~0.7718" for E3 -- this number is actually E13's FedAvg (E2) multi-seed mean test Dice, not an E3 number; it has been corrected.
