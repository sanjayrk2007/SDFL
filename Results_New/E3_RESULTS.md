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
| 0.0 | 1 | 0.5542 | 0.4265 |
| 0.001 | 1 | 0.5782 | 0.4533 |
| 0.01 | 1 | 0.4958 | 0.3658 |
| 0.1 | 1 | 0.5077 | 0.3711 |

**Best configuration:** mu = 0.001, val_dice = 0.5782

**Status:** Complete. Reproduced on `integration/sdfl-final-validation` at the script's documented 20-round default.
**Note:** This supersedes the previously conflicting E3 numbers in README.md (0.5782 @ 1 round) and FINAL_RESULTS.md (0.4924, round count unstated).
