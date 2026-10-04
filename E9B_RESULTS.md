# E9b — Temporal Security Causal Ablation

> Entry-point: `e9b_temporal_ablation.py`
> Branch: `mukesh/sdfl-completion`

---

## Overview

E9b evaluates which components of the SDFL temporal-security stack independently contribute to protection against retrospective breach. Each configuration row adds one additional security mechanism over the previous row (A→F), isolating the causal contribution of each layer.

---

## Protocol Disclosure

> **Important:** The segmentation utility metrics (Dice, IoU, Precision, Recall, HD95) in the ablation table are **pre-computed reference constants** from the E1–E8 experimental campaign. Because the ablation's purpose is to evaluate **protocol-level security properties** (acceptance rates, replay rejection, key destruction), not to re-train image segmentation models per configuration, the utility metrics are fixed across Rows B–F (all reflect the full SDFL pipeline E7/E8 checkpoint). The security and timing columns are empirically measured from live protocol execution.

---

## Ablation Configurations

| Row | Configuration | Encryption | HMAC Certificate | Temporal Expiry Enforced | Key Rotation | Key Destruction |
|-----|--------------|-----------|-----------------|--------------------------|--------------|----------------|
| **A** | Plain FedAvg | None | ✗ | ✗ | ✗ | ✗ |
| **B** | AES-GCM (Persistent Key) | AES-256-GCM | ✗ | ✗ | ✗ | ✗ |
| **C** | AES-GCM + Certificate/AAD | AES-256-GCM | ✓ | ✗ | ✗ | ✗ |
| **D** | AES-GCM + Cert + Expiry (Key Retained) | AES-256-GCM | ✓ | ✓ | ✗ | ✗ |
| **E** | AES-GCM + Cert + Expiry + Rotation (No Destruction) | AES-256-GCM | ✓ | ✓ | ✓ | ✗ |
| **F** | **Full SDFL** (All Mechanisms) | AES-256-GCM | ✓ | ✓ | ✓ | ✓ |

---

## Security Test Results

| Row | Timely Accept Rate | Expired Reject Rate | Replay Reject Rate | Tamper Reject Rate | Post-Expiry Breach Rate |
|-----|-------------------|--------------------|--------------------|-------------------|------------------------|
| **A** | 100% | — | — | — | **1.0** (no protection) |
| **B** | 100% | — | — | — | **1.0** (persistent key survives expiry) |
| **C** | 100% | — | — | 100% | **1.0** (no expiry enforcement) |
| **D** | 100% | 100% | — | 100% | **1.0** (key retained, so decryptable) |
| **E** | 100% | 100% | 100% | 100% | **1.0** (rotation without destruction) |
| **F** | 100% | 100% | 100% | 100% | **0.0** ← **Key destroyed — irreversible** |

### Key Finding
**Only Row F (Full SDFL)** achieves post-expiry breach rate = 0.0.
Key destruction (`destroy_round_key()`) is the sole mechanism that converts a practical cryptographic difficulty into an information-theoretic impossibility after round expiry.

---

## Reference Utility Metrics (from E7/E8 checkpoint — all DP rows B–F share the same trained model)

| Row | Config | Dice | IoU | Precision | Recall |
|-----|--------|------|-----|-----------|--------|
| **A** | Plain FedAvg (E2) | 0.7712 | 0.6818 | 0.8124 | 0.7340 |
| **B–F** | Full SDFL pipeline | 0.5338 | 0.4020 | 0.6120 | 0.5284 |

> The utility gap (A vs B–F) is driven by DP-SGD noise and non-IID heterogeneity, not by encryption overhead. The cryptographic operations are numerically lossless (AES-GCM is bit-exact; no rounding error introduced).
