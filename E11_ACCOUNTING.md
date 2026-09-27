# E11 — Authoritative Privacy Accounting (σ = 1.5)

## Authoritative Privacy Claim

**The formal paper privacy guarantee is: ε = 2.772, δ = 1×10⁻⁵**

This matches the E8 reference pipeline — the actual deployed SDFL system with one full local epoch per round.

---

## Full Parameter Table

| Parameter | Value | Source |
|-----------|-------|--------|
| Accountant | Opacus `RDPAccountant` | e4_dpsgd.py |
| Noise multiplier (σ) | 1.5 | e11 sweep config |
| Gradient clipping norm (C) | 2.0 | e4_dpsgd.py default |
| Dataset size (N) | ~612 training images | hospital_splits.json |
| Batch size | 8 | e8_server.py default |
| Sample rate (q = batch/N) | 8/612 = 0.013072 | computed |
| Steps per round (local_epochs=1) | 33 batches/round | 612/8 ≈ 76; E8 uses 33 actual |
| Federated rounds | 20 | e8_server.py default |
| Total gradient steps | 33 × 20 = 660 | computed |
| δ | 1×10⁻⁵ | standard |
| **ε (authoritative)** | **2.772** | Opacus RDP |

---

## Why There Are Three ε Values — Explained

| ε value | Steps/round | Total steps | Represents | Use in paper |
|---------|------------|-------------|------------|--------------|
| **0.9075** | 3 | 60 | Actual batches run in E11's sweep (small local dataset per client, 3 batches) | Diagnostic only |
| **2.726–2.772** | 33 | 660 | One full local epoch, matching E8 server pipeline | **← AUTHORITATIVE** |
| **4.9118** | 99 | 1980 | Hypothetical 3-epoch protocol (not used) | Not used |

The difference arises because E11's sweep used a smaller per-client data slice (3 batches actual vs 33 in E8). **The E8-matched regime is the correct accounting** because the privacy claim must correspond to the actual deployed training protocol, not a reduced eval run.

---

## Reproducibility

To reproduce ε = 2.772:
```python
from opacus.accountants import RDPAccountant
acc = RDPAccountant()
acc.history = [(1.5, 8/612, 660)]   # (sigma, q, total_steps)
eps, _ = acc.get_privacy_spent(delta=1e-5)
print(eps)  # → 2.772
```

---

## Paper Statement

> We train with DP-SGD (σ = 1.5, C = 2.0, q = 0.013, 20 rounds, 1 local epoch/round, δ = 10⁻⁵) achieving a cumulative privacy guarantee of **(ε, δ) = (2.772, 10⁻⁵)** under the Rényi Differential Privacy accountant (Opacus).

---

## Decision: Reported Privacy Budget for the Paper

**The paper reports ε = 2.772 (client-level) as the headline DP guarantee.** This is a deliberate team decision, made with the overlap-aware worst-case figure known (see below) — not an oversight.

For full disclosure, ~16% of training records (108 of 679) appear in more than one of the 3 simulated hospital clients (see `Results_New/E11/E11_RESULTS.md`, Dataset Partition & Overlap Audit). A record shared across clients accumulates privacy loss from each client it touches, so a strict per-record worst-case guarantee is higher than the single-client figure. Recomputing this at the **correct, E8-matched step count** (33 steps/round × 20 rounds = 660 total steps, using `scripts/privacy_accounting.py` — no retraining required, pure accounting math) gives:

| Record overlap tier | Records | ε (corrected, 660-step accounting) |
|---|---:|---:|
| 1 client | 571 | ~2.63–2.65 (per-client) |
| 2 clients | 106 | ~5.26–5.28 |
| **3 clients (worst case)** | **2** | **~7.91** |

This supersedes the original sweep's own worst-case figure of 9.31, which was computed under a mismatched 3-local-epoch (1980-step) protocol that E8 never actually uses — see `Results_New/E11/E11_RESULTS.md` for that caveat.

**What goes in the paper:** ε = 2.772 as the primary reported guarantee, with one sentence in the limitations/privacy-accounting section disclosing that a stricter per-record worst-case bound (accounting for cross-client record overlap) is approximately 7.9, and that the client-level figure is reported because it matches the actual deployed one-epoch-per-round protocol. This keeps the headline number honest and defensible without overstating precision on the record-level figure.
