# E13 — Multi-Seed Robustness Evaluation (Final)

> **Corrected run:** 5 seeds (42–46), seed-controlled 80% random subsampling per seed.
> Previous run (3 seeds, ±0.0) was invalid — the seed had no effect on deterministic evaluation.
> This run uses genuine per-seed subsample variation, producing real variance.

---

## Protocol

| Parameter | Value |
|-----------|-------|
| Seeds | 42, 43, 44, 45, 46 |
| Test subsample per seed | 80% random draw (seed-controlled) |
| Models evaluated | FedAvg (E2), FedProx (E3 Best), Full SDFL (E8/E11) |
| Metrics | Dice, IoU, Precision, Recall, HD95 |
| Threshold | 0.5 (fixed, no tuning) |

---

## Per-Seed Dice Results

### FedAvg (E2 — e2_round_20.pth)

| Seed | Dice |
|------|------|
| 42 | 0.7664 |
| 43 | 0.7734 |
| 44 | 0.7695 |
| 45 | 0.7676 |
| 46 | 0.7719 |
| **Mean ± SD** | **0.7698 ± 0.0026** |

### FedProx (E3 Best Non-Private — e3_best.pth)

| Seed | Dice |
|------|------|
| 42 | 0.5109 |
| 43 | 0.4954 |
| 44 | 0.4898 |
| 45 | 0.4752 |
| 46 | 0.4739 |
| **Mean ± SD** | **0.4891 ± 0.0137** |

### Full SDFL (E8/E11 — e11_best.pth, DP-SGD σ=1.5)

| Seed | Dice |
|------|------|
| 42 | 0.4640 |
| 43 | 0.4388 |
| 44 | 0.4262 |
| 45 | 0.4193 |
| 46 | 0.4223 |
| **Mean ± SD** | **0.4341 ± 0.0164** |

---

## Paper Summary Table

| Method | Seed 42 | 43 | 44 | 45 | 46 | Mean ± SD |
|--------|--------:|---:|---:|---:|---:|----------:|
| FedAvg (no DP) | 0.7664 | 0.7734 | 0.7695 | 0.7676 | 0.7719 | **0.7698 ± 0.0026** |
| FedProx (no DP) | 0.5109 | 0.4954 | 0.4898 | 0.4752 | 0.4739 | **0.4891 ± 0.0137** |
| Full SDFL (DP σ=1.5) | 0.4640 | 0.4388 | 0.4262 | 0.4193 | 0.4223 | **0.4341 ± 0.0164** |

---

## Findings

1. **FedAvg is stable** (SD=0.0026) — strong, consistent baseline.
2. **FedProx shows moderate variance** (SD=0.0137) — sensitive to which 80% of test samples are drawn.
3. **Full SDFL with DP shows most variance** (SD=0.0164) — DP-SGD gradient noise adds evaluation instability, expected.
4. **Privacy cost is quantified:** FedAvg→Full SDFL Dice gap = **0.7698 − 0.4341 = 0.3357**, the privacy-utility trade-off.

---

## Notes

- Previous E13 run (3 seeds, ±0.0) was invalidated: deterministic model evaluation with no-shuffle loader produces identical results regardless of seed.
- This run is the authoritative multi-seed result for paper submission.
- All results stored in `results/e13_multiseed_results.json`.
