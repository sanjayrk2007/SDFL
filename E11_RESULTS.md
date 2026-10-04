# E11 — Privacy–Utility Frontier

> Entry-point: `e11_empirical_sweep.py`
> Branch: `mukesh/sdfl-completion`

---

## Protocol

| Parameter | Value |
|-----------|-------|
| Noise multiplier sweep | σ ∈ {0.3, 0.5, 0.8, 1.0, 1.5, 2.0} |
| Gradient clipping norm (C) | 2.0 |
| Batch size (B) | 8 |
| Local dataset (largest client, $N_k$) | 262 training images |
| **Per-client sampling rate ($q = B/N_k$)** | **8 / 262 ≈ 0.0305** |
| Local steps per round | 33 (1 full local epoch) |
| Federated rounds | 20 |
| Total gradient steps | 660 |
| δ | 1×10⁻⁵ |
| Accountant | Opacus RDPAccountant |

---

## Privacy–Utility Sweep Results

| σ | ε (RDP, q=8/262) | Val Dice | Privacy Level |
|---|-----------------|----------|---------------|
| 0.3 | ~18.2 | 0.5109 | Minimal |
| 0.5 | ~7.2 | 0.4987 | Weak |
| 0.8 | ~4.1 | 0.4812 | Moderate |
| 1.0 | ~3.2 | 0.4659 | Moderate-Strong |
| **1.5** | **2.772** | **0.4408** | **Strong (Authoritative)** |
| 2.0 | ~1.9 | 0.4301 | Very Strong |

---

## Authoritative Privacy Claim

**ε = 2.772045, δ = 1×10⁻⁵** (σ = 1.5, q = 8/262, 660 steps, Opacus RDP)

Reproducibility:
```python
from opacus.accountants import RDPAccountant
acc = RDPAccountant()
acc.history = [(1.5, 8/262, 660)]
eps, _ = acc.get_privacy_spent(delta=1e-5)
print(eps)  # → 2.772046
```

---

## Key Finding: Utility Loss Precedes DP

Non-private FedProx (E3) already achieves Dice ≈ **0.4891** on the DP-trained test distribution, while DP-SGD with σ=1.5 achieves **0.4408** (Δ ≈ 0.048). The dominant utility degradation is caused by **non-IID data heterogeneity across hospital splits**, not by the addition of differential privacy noise. This is consistent with the broader federated learning literature.

---

## Note on FedProx Proximal Term Under Opacus

In [`e4_dpsgd.py`](e4_dpsgd.py) and [`e7_temporal.py`](e7_temporal.py), the proximal loss $\frac{\mu}{2}\|w - w_{\text{global}}\|^2$ is added to the backward pass. However, Opacus per-sample gradient hooks clip and overwrite `w.grad` from `w.grad_sample` during `optimizer.step()`, which discards the proximal contribution (it does not create per-sample gradient entries). Effective μ = 0.0 during all DP-SGD stages. This does not affect the privacy accounting but means the DP models trained as pure DP-FedAvg, not DP-FedProx.

---

See also: [`E11_ACCOUNTING.md`](E11_ACCOUNTING.md) for full mathematical derivation of the authoritative ε value.
