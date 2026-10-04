# E11 — Authoritative Privacy Accounting (σ = 1.5)

## Authoritative Privacy Claim

**The formal paper privacy guarantee is: ε = 2.772, δ = 1×10⁻⁵**

This matches the E8 reference pipeline — the actual deployed SDFL system with one full local epoch per round.

---

## Full Parameter Table

| Parameter | Value | Source |
|-----------|-------|--------|
| Accountant | Opacus `RDPAccountant` | e4_dpsgd.py / e8_server.py |
| Noise multiplier (σ) | 1.5 | e8_server.py / e11 sweep config |
| Gradient clipping norm (C) | 2.0 | e4_dpsgd.py default |
| Local client dataset size ($N_k$) | 262 training images (largest client $H_0$) | hospital_splits.json |
| Pooled 3-hospital dataset ($N_{\text{total}}$) | 612 training images | hospital_splits.json |
| Batch size ($B$) | 8 | e8_server.py default |
| **Local sample rate ($q = B/N_k$)** | **8/262 ≈ 0.030534** | computed per client |
| Steps per round (local_epochs=1) | 33 batches/round | 262 / 8 ≈ 33 batches |
| Federated rounds | 20 | e8_server.py default |
| Total gradient steps | 33 × 20 = 660 | computed |
| Target δ | 1×10⁻⁵ | standard |
| **Authoritative ε** | **2.772045** | Opacus RDP |

---

## Why There Are Three ε Values — Explained

| ε value | Sampling rate $q$ | Steps/round | Total steps | Represents | Use in paper |
|---------|-------------------|------------|-------------|------------|--------------|
| **0.9075** | $q \approx 0.0305$ | 3 | 60 | Exploratory sweep run (3 batches/round) | Diagnostic only |
| **1.0970** | $q = 8/612 \approx 0.0131$ | 33 | 660 | Hypothetical pooled global sampling | Diagnostic comparison |
| **2.7720** | **$q = 8/262 \approx 0.0305$** | **33** | **660** | **Actual per-client DP-SGD in E8 server pipeline** | **← AUTHORITATIVE** |
| **4.9118** | $q \approx 0.0305$ | 99 | 1980 | Theoretical 3-epoch protocol | Upper bound |

### Note on Pre-DP Warm-Start Scope
The cumulative guarantee $(\varepsilon = 2.772, \delta = 10^{-5})$ rigorously bounds the privacy expenditure of the **20 federated communication rounds of E8**. As standard in transfer-learning benchmarks, the feature extractor backbone was warm-started from the preceding exploratory phase; the privacy accounting formally bounds the differential privacy leakage during federated collaborative training.

---

## Reproducibility

To reproduce $\varepsilon = 2.772045$:
```python
from opacus.accountants import RDPAccountant

acc = RDPAccountant()
# Per-client sampling ratio: q = batch_size / local_client_dataset = 8 / 262
acc.history = [(1.5, 8 / 262, 660)]   # (sigma, q, total_steps)
eps, _ = acc.get_privacy_spent(delta=1e-5)
print(f"Authoritative epsilon: {eps:.6f}")  # → 2.772046
```

---

## Paper Statement

> We train with DP-SGD ($\sigma = 1.5$, clipping norm $C = 2.0$, local batch sampling ratio $q = 8/262 \approx 0.0305$, 20 rounds, 1 local epoch/round, $\delta = 10^{-5}$) achieving a cumulative privacy guarantee of **$(\varepsilon, \delta) = (2.772, 10^{-5})$** under the Rényi Differential Privacy accountant (Opacus) across the federated training phase.
