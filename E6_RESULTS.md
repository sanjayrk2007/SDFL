# Experiment E6 — Sanitization Pipeline

## Configuration

| Parameter | Value |
|---|---|
| **Model** | ResUNet++ with GroupNorm (num_groups=4) and non-inplace ReLU |
| **Framework** | Flower (flwr) + Ray simulation backend + Opacus DP-SGD |
| **Clients** | 3 (one per non-IID hospital split) |
| **Rounds** | 20 |
| **Local epochs per round** | 3 |
| **Proximal term μ** | 0.001 |
| **Clipping Norm (C)** | 2.0 |
| **Noise Multiplier (σ)** | 1.5 |
| **Symmetric Encryption** | AES-GCM (256-bit key) |
| **Sanitization Pipeline** | CLAHE, Text Artifact Removal (Inpainting), Metadata Scrub |
| **PHI Gate Threshold** | Inpaint ratio <= 0.05 |

---

## Results

Validation metrics and privacy spending comparison with E5 (baseline 0.4271):

| Experiment | val_dice | val_iou | ε (epsilon) | Skipped Samples |
|---|---|---|---|---|
| **E5 (Secure Aggregation)** | 0.4271 | 0.3111 | 0.9793 | N/A |
| **E6 (Sanitized Pipeline)** | 0.5400 | 0.4081 | 0.9793 | 257 |

**Status:** Complete. The patient privacy sanitization pipeline successfully ran on client partitions prior to training.
Skipped samples (failed PHI gate) were logged to `skipped_samples.log`.
The model checkpoint has been saved to `checkpoints/e6_best.pth`.
