# SDFL Integration Manifest & Experiment Baseline Freeze

> **Repository:** `sanjayrk2007/SDFL`  
> **Integration Branch:** `integration/sdfl-final-validation`  
> **Date:** September 13, 2026  
> **Status:** FROZEN FOR REPRODUCTION (Tier-1 & Tier-2 Validated)  

---

## 1. Lineage & Branch Tracking

| Component | Source Branch | Exact Git SHA |
| :--- | :--- | :--- |
| **Base Baseline** | `hospital-demo-fixes-threshold-fix` | `e5fe450f1a351badc790233f5f058364dbbbf4e0` |
| **Security Hardening (Sanjay)** | `sanjay/security-hardening` | `2212a7a77aea404d4ea6beb0d322b7a750f12d73` |
| **Experiment Infra (Sameer)** | `sameer/experiment-infrastructure` | `0c6449a34866f44db47d39e7a036c8b14c282659` |
| **Completion & Experiments (Mukesh)** | `mukesh/sdfl-completion` | `f86f812498cdb04f38bb4fc6eef3c9959743fc1d` |
| **Pre-Freeze Integration SHA** | `integration/sdfl-final-validation` | `0656ad51878fad6b9dd117b61a16de8288e9f0ef` |

---

## 2. Validation Evidence

### A. Tier-1 Integration Validation
* **Repository & Compilation:** `py_compile crypto.py e7_temporal.py e8_server.py scripts/*.py` passed cleanly (0 syntax errors, 0 untracked artifacts).
* **Cryptographic Unit Tests (`crypto.py`):** **14/14 passed** (0.02s) — Deterministic serialization, multi-layer, dtypes (f16, f32, f64, i32, i64), shapes, numerical preservation, AES-GCM tag verification, wrong-key / tampered-CT / modified-nonce / modified-AAD rejection, weighted aggregation, in-memory zeroization.
* **Temporal Security Suite (`e7_temporal.py --test_only`):** **All E7 tests passed** (0.95s) — Deterministic model & update hashing, HMAC certificate creation/signing/verification, expired submission rejection ($t \ge T_r$), client ID validation, replay rejection, AAD mismatch rejection, key destruction post-expiry, structured audit logging (`round_open`, `round_close`, `key_destroyed`).
* **E8 Production Boundary (`test_e8_integration.py`):** **8/8 pytest tests passed** (1.14s) — Production server AAD reconstruction from certificate metadata, prohibition of `associated_data=None`, sample-weighted client averaging, forward secrecy post key destruction.
* **Security Attack Smoke Test (`scripts/security_attacks.py --attempts_per_seed 20`):** **14/14 attack conditions evaluated across 5 seeds** (0.08s) — 100% acceptance for legitimate updates, 0.0% attack success across 13 adversarial vectors.
* **Hospital Demo Invariant Check (`sdfl-demo/`):** Full demo present; `UNCERTAINTY_THRESHOLD = 0.00295` preserved in `sdfl-demo/app.py`; FastAPI routes, model definitions, and inference logic import cleanly.
* **Experiment Infrastructure:** All modules (`e9_breach_attack`, `e9b_temporal_ablation`, `e10_window_sweep`, `e11_empirical_sweep`, `e11_privacy_utility`, `e12_unseen_hospital`, `e13_multiseed`, `e14_scalability`, `e15_fault_robustness`, `scripts/*.py`) import with zero errors.

### B. Tier-2 End-to-End SDFL Integration Smoke Test
* **Execution Script:** `scratch/test_tier2_e2e.py`
* **Test Architecture:** 3 Hospital Clients $\to$ 1 Round $\to$ Opacus DP-SGD Local Training $\to$ Model Hashing $\to$ Certificate Signing $\to$ AES-GCM Encryption with Canonical AAD $\to$ Server Validation $\to$ AAD Reconstruction $\to$ Decryption $\to$ Sample-Weighted Aggregation $\to$ Global Model Update $\to$ Key Destruction $\to$ Round 2 Re-initialization $\to$ Audit Log Trace.
* **Result:** **TIER-2 PASSED** — Real production classes (`FullSDFLStrategy`, `FullSDFLClient`, `ResUNetPlusPlus`, `crypto.py`) executed the entire federated lifecycle with in-memory zeroization and forward secrecy verified.

---

## 3. Environment & Dependencies

* **Python:** 3.14.6 (macOS arm64 / Linux x86_64 compatible)
* **PyTorch:** 2.12.1 (CUDA 12.x / MPS / CPU)
* **TorchVision:** 0.27.1
* **Flower (`flwr[simulation]`):** 1.32.1
* **Opacus:** 1.6.0
* **Cryptography:** 46.0.7
* **NumPy:** 1.26.4 (`numpy < 2.0` enforced)
* **SciPy:** 1.17.1
* **Specification File:** `requirements.txt`

---

## 4. Security Core Invariants & Demo Baseline

1. **Authoritative Hardened Files:** `crypto.py`, `e7_temporal.py`, `e8_server.py`, `test_e8_integration.py`, `scripts/security_attacks.py`.
2. **Canonical AAD Binding:** Reconstructed deterministically from certificate `(round_id, client_id, model_hash, key_context_id)`; `associated_data=None` is strictly forbidden in production update decryption.
3. **Demo & Patent Assets:** `sdfl-demo/` directory intact; `UNCERTAINTY_THRESHOLD = 0.00295`; finalized patent document `SDFL_Patent_Final_NEW.pdf` preserved.

---

## 5. Explicit Experiment-Status Registry (E1–E15)

> **Notice on Historical Results:** All existing `.json`, `.jsonl`, and `.md` results in `results/` represent historical reference runs from development branches. They MUST NOT be cited as final paper results until explicitly reproduced on the frozen SHA.

| Experiment | Title / Focus | Authoritative Entry-Point Script | Code Present | Integration-Tested | Result on Frozen SHA | Colab / GPU Required | Notes & Execution Requirements |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **E1** | Centralized Baseline | `e1_centralized.py` | ✅ Yes | ✅ Yes | Historical | Yes (GPU) | 50 epochs, Kvasir-SEG dataset. |
| **E2** | FedAvg Baseline | `e2_server.py` | ✅ Yes | ✅ Yes | Historical | Yes (GPU) | 20 rounds, 3 clients, `hospital_splits.json`. |
| **E3** | FedProx Non-IID | `e3_fedprox.py` | ✅ Yes | ✅ Yes | Historical | Yes (GPU) | $\mu=0.001$, 20 rounds. |
| **E4** | DP-SGD Integration | `e4_dpsgd.py` | ✅ Yes | ✅ Yes | Historical | Yes (GPU) | $C=2.0, \sigma=1.5$, GroupNorm conversion. |
| **E5** | SecAgg Key Exchange | `e5_secagg.py` | ✅ Yes | ✅ Yes | Historical | Yes (GPU) | AES-256-GCM authenticated payload encapsulation. |
| **E6** | Input Sanitization | `e6_server.py` | ✅ Yes | ✅ Yes | Historical | Yes (GPU) | Outlier rejection & mask pre-validation. |
| **E7** | Temporal Checkpointing | `e7_temporal.py` | ✅ Yes | ✅ Yes (Tier-1) | Historical | Optional | `--test_only` runs on CPU (0.9s); full training requires GPU. |
| **E8** | Full SDFL Production FL | `e8_server.py` | ✅ Yes | ✅ Yes (Tier-2) | Historical | Yes (GPU) | 20 rounds, requires `checkpoints/e7_best.pth` (or `e6_best.pth`). |
| **E9** | Retrospective Breach | `e9_breach_attack.py` | ✅ Yes | ✅ Yes (Tier-1) | Historical | No (CPU) | 5,000 attack attempts across 5 threat models (~3s). |
| **E9b** | Temporal Causal Ablation | `e9b_temporal_ablation.py` | ✅ Yes | ✅ Yes | Historical | No (CPU) | Evaluates causal impact of key destruction (~2s). |
| **E10** | Temporal Window Sweep | `e10_window_sweep.py` | ✅ Yes | ✅ Yes | Historical | No (CPU) | Parameterized latency simulation ($T_r \in [30\text{s}, 1200\text{s}]$). |
| **E11** | Privacy–Utility Frontier | `e11_empirical_sweep.py` / `scripts/privacy_accounting.py` | ✅ Yes | ✅ Yes | Historical | Yes (GPU) for sweep | Sweep across $\sigma \in [0.3, 2.0]$; RDP accounting runs on CPU. |
| **E12** | LOCO Generalization | `e12_unseen_hospital.py` | ✅ Yes | ✅ Yes | Historical | Yes (GPU) | 3-fold leave-one-centre-out training (~1.5h on GPU). |
| **E13** | Multi-Seed Evaluation | `e13_multiseed.py` | ✅ Yes | ✅ Yes | Historical | Optional | 5 seeds ($42–46$) with 80% subsampling on existing checkpoints. |
| **E14** | Cohort Scalability | `e14_scalability.py` | ✅ Yes | ✅ Yes | Historical | No (CPU/GPU) | Benchmarks $K \in \{3, 5, 10, 20\}$ clients (~10s). |
| **E15** | Fault & Robustness Suite| `e15_fault_robustness.py` | ✅ Yes | ✅ Yes | Historical | No (CPU) | 10 fault & anomaly injection scenarios (~5s). |

---

## 6. Colab Reproduction Specification & Execution Requirements

### A. General Execution Rules
1. **Repository Cloning:** Must check out the exact frozen integration commit SHA.
2. **Dataset Setup:** Kvasir-SEG dataset containing `images/` and `masks/` placed in `data/kvasir-seg/` (or symlinked), with `hospital_splits.json` present at repository root.
3. **Hardware Tiers:**
   - **GPU Required:** E1, E2, E3, E4, E5, E6, E8, E11 (training sweep), E12. (NVIDIA T4 / V100 / A100 with $\ge 12\text{GB}$ VRAM).
   - **CPU-Only Friendly:** E7 (verification), E9, E9b, E10, E11 (accounting only), E13 (evaluating checkpoints), E14, E15.
4. **Seed Control:** Multi-seed evaluations (E9, E13) strictly fix random seeds to $[42, 43, 44, 45, 46]$.

---

## 7. Known Scientific & Methodological Boundaries

1. **Retrospective Threat Boundary (E9):** SDFL bounds retrospective exposure post-round ($t > T_r$); it assumes secure execution memory during the ephemeral aggregation window while the key is active in RAM.
2. **Simulated Node Delays (E10):** Latencies in E10 represent parameterized clinical node delay distributions ($H_0, H_1, H_2$) rather than physical WAN telemetry.
3. **Formal Privacy Guarantee (E11):** The authoritative privacy bound is **$(\varepsilon = 2.772, \delta = 10^{-5})$** under Opacus RDP (660 steps, 1 local epoch/round, 20 rounds, $\sigma=1.5, C=2.0$).
4. **Synthetic Client Splits (E12):** Dataset partitions are synthetic size-biased subsets of Kvasir-SEG.
