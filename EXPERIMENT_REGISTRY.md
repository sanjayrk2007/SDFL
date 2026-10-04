# SDFL Experiment Registry — E1 to E15

> **Last Updated:** 2026-10-04
> **Canonical Branch:** `mukesh/sdfl-completion` (Mukesh) | `origin/integration/sdfl-final-validation` (full team)

---

## Ownership Policy

| Owner | Files Owned |
|-------|-------------|
| **Sanjay** | `crypto.py`, `e7_temporal.py`, `e8_server.py`, `test_e8_integration.py` |
| **Mukesh** | `e4_dpsgd.py`, `e11_empirical_sweep.py`, `e12_unseen_hospital.py`, `e13_multiseed.py`, `e14_scalability.py`, `e15_fault_robustness.py`, `scripts/privacy_accounting.py`, `scripts/privacy_utility_sweep.py`, `scripts/cross_centre_evaluation.py`, `scripts/multiseed_runner.py` |
| **Sameer** | `scripts/sanitize.py`, `scripts/experiment_runner.py`, `scripts/temporal_window_experiment.py`, `scripts/scalability_experiment.py`, `scripts/fault_injection.py`, `sdfl-demo/` |
| **Shared (do not modify without team approval)** | `model.py`, `config.py`, `scripts/dataset.py`, `scripts/joint_transforms.py`, `hospital_splits.json`, `splits.json` |

---

## Full Experiment Status

| Exp | Title | Owner | Script | Status | Paper-Ready | Key Result |
|-----|-------|-------|--------|--------|-------------|------------|
| **E1** | Centralized Baseline | Sameer | `e1_centralized.py` | ✅ Complete | ✅ YES | Dice = **0.8182** (50 epochs, Kvasir-SEG) |
| **E2** | FedAvg Baseline | Sameer | `e2_server.py` | ✅ Complete | ✅ YES | Dice = **0.7718** (20 rounds, 3 clients) |
| **E3** | FedProx Non-IID Sweep | Mukesh | `e3_fedprox.py` | ✅ Complete | ✅ YES | Best μ=0.001, Dice = **0.5782** (Round 1) |
| **E4** | DP-SGD Integration | Mukesh | `e4_dpsgd.py` | ✅ Complete | ✅ YES | σ=1.5, C=2.0, GroupNorm conversion |
| **E5** | Authenticated Update Encryption | Sameer | `e5_secagg.py` | ✅ Complete | ✅ YES | AES-256-GCM; lossless parameter transport |
| **E6** | Input Sanitization | Sanjay | `e6_server.py` | ✅ Complete | ✅ YES | CLAHE + Telea inpainting; 5% area threshold |
| **E7** | Temporal Checkpointing | Sanjay | `e7_temporal.py` | ✅ Complete | ✅ YES | All 7 temporal protocol tests passed |
| **E8** | Full SDFL Production FL | Shared | `e8_server.py` | ✅ Complete | ✅ YES | Dice(ID)=0.4145, Dice(OOD)=0.4869, ε=2.772 |
| **E9** | Retrospective Breach Attack | Mukesh | `e9_breach_attack.py` | ✅ Complete | ✅ YES | 0/5,000 breaches; per-condition UB < 0.3% |
| **E9b** | Temporal Causal Ablation | Sanjay | `e9b_temporal_ablation.py` | ✅ Complete | ✅ YES | Row E breach=1.0, Row F breach=0.0 (key destruction essential) |
| **E10** | Temporal Window Sweep | Mukesh | `e10_window_sweep.py` | ✅ Complete | ✅ YES | Tr=120s → 100% availability |
| **E11** | Privacy–Utility Frontier | Mukesh | `e11_empirical_sweep.py` | ✅ Complete | ✅ YES | σ=1.5, **ε=2.772** (q=8/262), Dice=0.4408 |
| **E12** | Synthetic Client-Holdout Ablation | Mukesh | `e12_unseen_hospital.py` | ✅ Complete | ✅ YES (Disclosed) | Macro Dice=**0.2190** (plain FedAvg, 3-fold LOCO) |
| **E13** | Multi-Seed Test Variability | Mukesh | `e13_multiseed.py` | ✅ Complete | ✅ YES (Disclosed) | FedAvg 0.7698±0.0026; SDFL 0.4341±0.0164 (5 seeds, 80% subsample) |
| **E14** | Client Scalability Benchmark | Mukesh | `e14_scalability.py` | ✅ Complete | ✅ YES (Disclosed) | Linear O(K) scaling, 361ms→1332ms (AMD64 CPU) |
| **E15** | Fault & Robustness Suite | Mukesh/Sameer | `e15_fault_robustness.py` | ✅ Complete | ✅ YES | 10/10 fault scenarios passed |

---

## Mukesh Deliverables Summary (All Complete ✅)

| Deliverable | File | Status |
|-------------|------|--------|
| DP-SGD client implementation | `e4_dpsgd.py` | ✅ Complete |
| Privacy accounting utility | `scripts/privacy_accounting.py` | ✅ Complete (q=8/262 corrected) |
| Privacy-utility sweep wrapper | `scripts/privacy_utility_sweep.py` | ✅ Complete |
| Cross-centre evaluation | `scripts/cross_centre_evaluation.py` | ✅ Complete |
| Multi-seed runner | `scripts/multiseed_runner.py` | ✅ Complete |
| E10 Window Sweep | `e10_window_sweep.py` | ✅ Complete |
| E11 Privacy Sweep | `e11_empirical_sweep.py` | ✅ Complete |
| E11 Accounting (corrected) | `E11_ACCOUNTING.md` | ✅ Complete (q=8/262, ε=2.772) |
| E12 LOCO Ablation | `e12_unseen_hospital.py` + `E12_LOCO_INTEGRITY.md` | ✅ Complete |
| E13 Test Variability | `e13_multiseed.py` (5 seeds, 80% subsample) | ✅ Complete |
| E14 Scalability (with hardware spec) | `e14_scalability.py` + `E14_RESULTS.md` | ✅ Complete |
| E15 Fault Robustness | `e15_fault_robustness.py` | ✅ Complete |
| Experiment Registry | `EXPERIMENT_REGISTRY.md` | ✅ This file |

---

## Known Disclosures (Must Appear in Paper)

| Topic | Disclosure Required |
|-------|-------------------|
| FedProx + Opacus | Proximal term $\frac{\mu}{2}\|w-w_t\|^2$ is dropped by Opacus per-sample hooks during `optimizer.step()`. Effective μ = 0.0 in all DP stages. |
| ε scope | ε = 2.772 applies to the 20-round E8 federated phase only. Backbone warm-started from non-private E3/E7 exploration. |
| ε sampling rate | q = 8/262 (per-client local batch sampling), not q = 8/612 (pooled dataset). |
| E9 attack substrate | Synthetic float32 tensors, not real gradients. A5 is a noisy-vector proxy. 0.3% bound is per-condition, not pooled. |
| E9b utility constants | Dice/IoU for Rows B–F are pre-computed constants from E7/E8 campaign; only security properties are live-measured. |
| E12 client type | Synthetic overlapping subsets of Kvasir-SEG, not independently collected hospital data. |
| E13 methodology | Test-set subsampling variance across fixed checkpoints, not independent full retraining. |
| E14 latency | Hardware-dependent; communication/storage numbers are hardware-independent. |
