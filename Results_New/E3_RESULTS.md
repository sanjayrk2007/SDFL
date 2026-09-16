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

**Best configuration:** mu = 0.01, val_dice = 0.8569

**Status:** Complete. Reproduced on `integration/sdfl-final-validation` at the script's documented 20-round default.
**Note:** This supersedes the previously conflicting E3 numbers in README.md (0.5782 @ 1 round) and FINAL_RESULTS.md (0.4924, round count unstated).
