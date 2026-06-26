# Experiment E4 — DP-SGD Integration

## Configuration

| Parameter | Value |
|---|---|
| **Model** | ResUNet++ with BatchNorm2d → GroupNorm(num_groups=4), inplace=False ReLU |
| **Framework** | Flower (flwr) + Ray simulation backend + Opacus PrivacyEngine |
| **Clients** | 3 (one per non-IID hospital split) |
| **Rounds** | 1 |
| **Local epochs per round** | 3 |
| **Proximal term μ** | 0.001 (from E3 best configuration/checkpoint) |
| **Target Privacy Budget** | δ = 10⁻⁵ |

---

## Sweep Configurations

Grid search over:

- Gradient clipping norm **C** ∈ {0.5, 1.0, 2.0}
- Noise multiplier **σ** ∈ {0.5, 1.0, 1.5}

---

## Sweep Results

Validation metrics (Dice and IoU) and privacy spending (ε) for 1 round of federated training:

| C | σ | val_dice | val_iou | ε (epsilon) |
|:---:|:---:|:---:|:---:|:---:|
| 0.5 | 0.5 | 0.4305 | 0.3145 | 12.6931 |
| 0.5 | 1.0 | 0.4276 | 0.3112 | 2.1410 |
| 0.5 | 1.5 | 0.4283 | 0.3116 | 0.9793 |
| 1.0 | 0.5 | 0.4298 | 0.3140 | 12.6931 |
| 1.0 | 1.0 | 0.4259 | 0.3094 | 2.1410 |
| 1.0 | 1.5 | 0.4307 | 0.3139 | 0.9793 |
| 2.0 | 0.5 | 0.4245 | 0.3086 | 12.6931 |
| 2.0 | 1.0 | 0.4290 | 0.3126 | 2.1410 |
| **2.0** | **1.5** | **0.4312** | **0.3145** | **0.9793** |

---

## Best Tradeoff Configuration

| Parameter | Value |
|---|---|
| **Clipping Norm (C)** | 2.0 |
| **Noise Multiplier (σ)** | 1.5 |
| **Validation Dice** | 0.4312 |
| **Validation IoU** | 0.3145 |
| **Epsilon (ε)** | 0.9793 |
| **Delta (δ)** | 1e-5 |

**Status:** Sweep complete. The best tradeoff configuration provides sub-1.0 differential privacy (ε = 0.9793, δ = 1e-5) while maintaining a validation Dice score of 0.4312 after 1 round of federated learning starting from the E3 checkpoint. E3 checkpoint.
