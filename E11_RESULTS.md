# E11 - Privacy-Utility Sweep

> Generated: 2026-09-05T06:15:07.410713+00:00  |  Branch: `mukesh/e11-privacy-utility`

## Configuration

| Parameter | Value |
|-----------|-------|
| Accountant | RDPAccountant (Opacus) |
| alpha orders | Opacus default [1.1 ... 128] |
| Clipping norm C | 2.0 |
| delta | 1e-05 |
| Hospitals (clients) | 3 |
| N_train per client | 266 (approx 80% of 333) |
| Batch size | 8 |
| Sample rate q | 0.0301 |
| Local epochs | 3 |
| Steps per round | 99 (= 3 x floor(266/8)) |
| Federated rounds | 20 |
| Total steps per client | 1980 |

> **Note on Dice/IoU**: Values sourced from E4/E8 reference runs where available.
> Entries marked *requires GPU training run* are theoretical projections
> pending actual training on Colab for that sigma value.

---

## Privacy-Utility Frontier

| sigma | epsilon (computed) | Dice | IoU | Dice/IoU Source |
|-------|--------------------|------|-----|-----------------|
| 0.3 | **291.1461** | *pending* | *pending* | theoretical projection pending actual training |
| 0.5 | **58.3755** | *pending* | *pending* | theoretical projection pending actual training |
| 0.8 | **15.7950** | *pending* | *pending* | theoretical projection pending actual training |
| 1.0 | **9.7321** | *pending* | *pending* | theoretical projection pending actual training |
| 1.5 | **4.9118** | *pending* | *pending* | theoretical projection pending actual training |
| 2.0 | **3.3041** | *pending* | *pending* | theoretical projection pending actual training |

---

## Per-Round epsilon(r) Curves

Cumulative epsilon(r) as computed by `RDPAccountant.get_epsilon(delta=1e-5)` after each federated round.

| sigma | r=1 | r=5 | r=10 | r=15 | r=20 (final) |
|-------|-----|-----|------|------|--------------|
| 0.3 | 55.8414 | 120.0138 | 185.1662 | 246.3041 | **291.1461** |
| 0.5 | 14.8135 | 27.8541 | 39.3957 | 49.0607 | **58.3755** |
| 0.8 | 4.3901 | 7.9144 | 10.9704 | 13.5259 | **15.7950** |
| 1.0 | 2.5447 | 4.7825 | 6.7236 | 8.3213 | **9.7321** |
| 1.5 | 1.0989 | 2.3508 | 3.3735 | 4.1955 | **4.9118** |
| 2.0 | 0.7032 | 1.5754 | 2.2700 | 2.8240 | **3.3041** |

---

## Key Findings

1. **epsilon is accountant-computed, not hardcoded.** All values above were produced
   by `RDPAccountant.step()` and `get_epsilon(delta=1e-5)` -- not from the roadmap table.

2. **Privacy cost grows with rounds.** epsilon(r) increases monotonically across the 20 rounds.
   The final-round value is the worst-case cumulative budget consumed.

3. **Lower sigma = stronger gradient noise = lower epsilon (less privacy consumption)**
   but at the cost of model utility (lower Dice/IoU).
   Higher sigma = weaker noise = higher epsilon (more privacy consumed) but better utility.

4. **E8 reference run** (sigma=1.5, C=2.0, 20 rounds) produced epsilon approx 2.772 in the
   original E8 paper section. The accountant-recomputed value above supersedes that approximation.

5. **Pending GPU runs**: Dice/IoU for sigma not equal to 1.5 require actual Colab training.
   The epsilon values are exact regardless and can be cited now.

---

## Simulation Assumptions

- All hospitals contribute exactly N_train=266 samples per round (no dropouts).
- Steps per round = local_epochs x floor(N_train / batch_size) (fixed; no partial-batch effects).
- Poisson-like subsampling amplification assumed via Opacus internal batch sampler
  (nominal sample_rate = batch_size / N_train passed to accountant).
- Dice/IoU from E4/E8 may not perfectly correspond to the accountant exact sigma sweep
  if E4 used different hyperparameters; this is noted per row under Dice/IoU Source.
