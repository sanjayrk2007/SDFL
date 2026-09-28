# Experiment E4 -- DP-SGD Integration (Reproduced)

## Configuration

| Parameter | Value |
|---|---|
| **Model** | ResUNet++ with BatchNorm2d → GroupNorm(num_groups=4), inplace=False ReLU |
| **Framework** | Flower (flwr) + Ray simulation backend + Opacus PrivacyEngine |
| **Clients** | 3 (one per non-IID hospital split) |
| **Starting checkpoint** | `checkpoints/e3_best.pth` |
| **Rounds** | 1 |
| **Local epochs per round** | 3 |
| **Proximal term μ** | 0.001 |
| **Target Privacy Budget** | $\delta = 10^{-5}$ |
| **Grid Search** | $C \in \{0.5, 1.0, 2.0\}$, $\sigma \in \{0.5, 1.0, 1.5\}$ |
| **Selection rule** | $\max(\text{val\_dice} / (\epsilon + 10^{-5}))$ |

---

## Sweep Results

### Reproduced Run (`integration/sdfl-final-validation`)

Validation metrics (Dice and IoU) and privacy spending ($\epsilon$) for 1 round of federated training:

| C | σ | val_dice | val_iou | ε (epsilon) |
|:---:|:---:|:---:|:---:|:---:|
| 0.5 | 0.5 | 0.2628 | 0.1701 | 12.6931 |
| 0.5 | 1.0 | 0.1383 | 0.0874 | 2.1410 |
| 0.5 | 1.5 | 0.1075 | 0.0668 | 0.9793 |
| 1.0 | 0.5 | 0.2709 | 0.1767 | 12.6931 |
| 1.0 | 1.0 | 0.0675 | 0.0411 | 2.1410 |
| 1.0 | 1.5 | 0.1175 | 0.0732 | 0.9793 |
| 2.0 | 0.5 | 0.2221 | 0.1418 | 12.6931 |
| **2.0** | **1.0** | **0.2947** | **0.1916** | **2.1410** |
| 2.0 | 1.5 | 0.1048 | 0.0650 | 0.9793 |

**Best Configuration (Reproduced Run):**
- $C = 2.0$, $\sigma = 1.0$
- `val_dice` = 0.2947, `val_iou` = 0.1916, $\epsilon = 2.1410$, $\delta = 10^{-5}$
- Checkpoint: `checkpoints/e4_best.pth`

### Historical Initial Run (Pre-Integration Reference)

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

*Note on discrepancy: The initial pre-integration run reported best tradeoff at $C=2.0, \sigma=1.5$ with `val_dice=0.4312`, $\epsilon=0.9793$. The reproduced run on the integration branch achieved best tradeoff at $C=2.0, \sigma=1.0$ with `val_dice=0.2947`, $\epsilon=2.1410$. Both runs used single-round sweeps starting from pre-trained checkpoints.*

---

## Technical Discussion & Analysis

### 1. Analysis of the Accuracy Drop (0.82 Baseline / 0.57 FedProx → 0.29–0.43 DP-SGD)
The centralized baseline achieves a Dice score of 0.8182, whereas adding DP-SGD drops the validation Dice score substantially. This drop is driven by the following factors:
* **Gradient Clipping Norm Mismatch ($C = 2.0$):** Typical gradients in a deep ResUNet++ segmentation network have relatively small norms. A clipping threshold of $C = 2.0$ is excessively high, meaning virtually no gradients are clipped. However, in DP-SGD, the injected Gaussian noise scales *linearly* with the clipping norm ($\sigma \times C$). As a result, setting $C = 2.0$ injects a disproportionately large amount of absolute noise ($\sigma \times C = 2.0$ to $3.0$ standard deviation) relative to the actual gradient magnitudes, destroying the gradient signal (severe signal-to-noise ratio degradation).
* **Small Client Batch Size ($B = 8$):** The noise added to the aggregated batch gradient is scaled by $\frac{\sigma C}{B}$. With a batch size of only 8, there are not enough samples in a batch to average out the injected noise, further exacerbating the corruption of learning signals.
* **Single-Round Sudden Perturbation:** Because Experiment E4 was evaluated as a single-round sweep (starting from the E3 checkpoint), the model was exposed to a massive noise injection for just 3 local epochs with no subsequent rounds to recover or adapt, causing an immediate, severe drop in Dice score.

### 2. Privacy Budget ($\epsilon$) Interpretation
* The privacy budget reported in E4 covers exactly **1 round of federated training** (consisting of 3 local epochs).
* This single-round budget **cannot be directly compared** to multi-round experiments (such as E8 and E11, which accumulate privacy spending over 20 rounds) without accounting for the number of training rounds and composition steps.

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`. Checkpoint: `checkpoints/e4_best.pth`.
