# Experiment E3 — FedProx Integration

## Configuration

| Parameter | Value |
|---|---|
| **Model** | ResUNet++ |
| **Framework** | Flower (flwr) + Ray simulation backend |
| **Clients** | 3 (one per non-IID hospital split) |
| **Rounds** | 1 |
| **Local epochs per round** | 3 |

---

## Sweep Configurations

Grid search over proximal term parameter:
- **μ** ∈ {0.0, 0.001, 0.01, 0.1}

*Note: $\mu = 0.0$ corresponds to E2 (FedAvg) and serves as our baseline.*

---

## Sweep Results

Validation metrics (Dice and IoU) for 1 round of federated training:

| μ | val_dice | val_iou |
|:---:|:---:|:---:|
| 0.0 | 0.5542 | 0.4265 |
| **0.001** | **0.5782** | **0.4533** |
| 0.01 | 0.4958 | 0.3658 |
| 0.1 | 0.5077 | 0.3711 |

---

## Best Configuration

| Parameter | Value |
|---|---|
| **Proximal term (μ)** | 0.001 |
| **Validation Dice** | 0.5782 |
| **Validation IoU** | 0.4533 |

**Status:** Sweep complete. The best configuration of $\mu = 0.001$ improves the validation Dice score to 0.5782 compared to the baseline FedAvg ($\mu = 0.0$, Dice = 0.5542) after 1 round.
