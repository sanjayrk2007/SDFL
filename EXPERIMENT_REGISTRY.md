# SDFL Experiment Registry

> **Branch:** `mukesh/sdfl-completion` (original); numeric corrections below reconciled against `integration/sdfl-final-validation`'s `Results_New/` on 2026-09-26.
> **Last updated:** 2026-09-12 (see 2026-09-26 corrections in the table below)
> **Owners:** Mukesh (ML/DP/Security), Sanjay (Crypto/Temporal), Sameer (Segmentation baseline)
>
> **Note (2026-09-26):** This table had several copy-paste errors between rows (E2 had E8's numbers, E3 had E13's number,
> E13's std values were fabricated as ±0.0000, E14's numbers were stale). The specific errors found have been corrected
> in place below. For the complete, cross-checked set of numbers across all 15 experiments, use
> `Results_New/results/MASTER_RESULTS.{csv,json,tex}` and `MASTER_RESULTS_SECURITY.{csv,json,tex}` instead of this table.
> `SDFL_Preflight_Audit.md`, referenced in the old E3 row, does not exist on `integration/sdfl-final-validation`.

---

## Registry

| Exp ID | Title | Owner | Script | Results | Status | Key Numbers |
|--------|-------|-------|--------|---------|--------|-------------|
| E1 | Dataset preparation & splits | Sameer | `scripts/dataset.py` | `hospital_splits.json` | DONE | 3 hospitals, Kvasir-SEG (612 train) |
| E2 | FedAvg baseline | Sameer | `e2_server.py` | `Results_New/results/e2_metrics.json` | DONE | Test Dice 0.7791 (the "0.4145 in-dist / 0.4869 OOD" previously listed here are E8's numbers, not E2's -- corrected) |
| E3 | FedProx μ sweep | Mukesh | `e3_fedprox.py` | `Results_New/results/e3_metrics.json`, `Results_New/E3_RESULTS.md` | DONE | Best μ=0.01: val Dice 0.8569, test Dice 0.4926 (the "~0.7718" previously listed here was E13's FedAvg multi-seed mean, not an E3 number -- corrected) |
| E5 | DP-SGD integration | Mukesh | `e4_dpsgd.py` | `results/e4_dpsgd_results.json` | DONE | ε=2.772, δ=1e-5 at σ=1.5 |
| E7 | Temporal security protocol | Sanjay | `e7_temporal.py` | `results/e8_metrics.json` | DONE | 0% post-expiry decrypt success |
| E8 | Full SDFL server eval | Shared | `e8_server.py` | `results/e8_metrics.json` | DONE | Combined DP+temporal+crypto |
| E9 | Breach attack simulation | Mukesh | `e9_breach_attack.py` | `results/e9_breach_results.json` | DONE | 0/5000 breaches succeeded |
| E9b | Temporal ablation (key destruction) | Sanjay | `e9b_temporal_ablation.py` | `results/e9b_temporal_results.json` | DONE | Row E: 100% success; Row F: 0% |
| E10 | Temporal window sweep | Mukesh | `e10_window_sweep.py` | `results/e10_window_results.json` | DONE | Tr=120s → 100% round completion |
| E11 | Privacy-utility sweep (σ grid) | Mukesh | `e11_empirical_sweep.py` | `results/e11_training_results.json` | DONE | σ=1.5: ε=4.91 (nominal) / 0.91 (executed) |
| E12 | Leave-one-client-out generalisation | Mukesh | `e12_unseen_hospital.py` | `results/e12_unseen_results.json` | DONE | Macro Mean Dice 0.2190; Worst 0.1579 |
| E13 | Multi-seed robustness | Mukesh | `e13_multiseed.py` | `Results_New/E13/e13_multiseed_results.json` | DONE | FedAvg 0.7698±0.0026; FedProx 0.4891±0.0137; SDFL 0.4341±0.0164 (5 seeds: 42-46; the "±0.0000" previously listed here was wrong -- these are computed directly from the per-seed values already in the committed JSON, not a rerun) |
| E14 | Security layer scalability (K clients) | Mukesh | `e14_scalability.py` | `Results_New/E14/e14_scalability_results.json` | DONE | K=3→231.9 ms; K=20→903.6 ms, roughly linear (the "179/752 ms" previously listed here were stale, from an earlier run on `mukesh/sdfl-completion` -- corrected to match the currently committed `Results_New` run) |
| E15 | Fault & late-client robustness | Mukesh | `e15_fault_robustness.py` | `results/e15_fault_results.json` | DONE | 10/10 scenarios PASSED |

---

## Mukesh Deliverables

| Deliverable | File | Status |
|-------------|------|--------|
| DP-SGD implementation | `e4_dpsgd.py` | DONE |
| Privacy accounting utility | `scripts/privacy_accounting.py` | DONE |
| Privacy-utility sweep | `scripts/privacy_utility_sweep.py` | DONE |
| Cross-centre evaluator | `scripts/cross_centre_evaluation.py` | DONE |
| Multi-seed runner | `scripts/multiseed_runner.py` | DONE |
| E9 breach attack | `e9_breach_attack.py` | DONE |
| E10 window sweep | `e10_window_sweep.py` | DONE |
| E11 empirical sweep | `e11_empirical_sweep.py` | DONE |
| E12 LOCO generalisation | `e12_unseen_hospital.py` | DONE |
| E13 multi-seed eval | `e13_multiseed.py` | DONE |
| E14 scalability bench | `e14_scalability.py` | DONE |
| E15 fault robustness | `e15_fault_robustness.py` | DONE |
| Final synthesis | `FINAL_RESULTS.md` | DONE |

---

## Common/Shared Deliverables

| Deliverable | File | Owner | Status |
|-------------|------|-------|--------|
| Experiment registry | `EXPERIMENT_REGISTRY.md` | Shared (Mukesh created) | DONE |
| Dataset splits | `hospital_splits.json` | Sameer | DONE |
| Dataset loader | `scripts/dataset.py` | Sameer | DONE |
| Joint transforms | `scripts/joint_transforms.py` | Sameer | DONE |
| Crypto module | `crypto.py` | Sanjay | DONE |
| Temporal security | `e7_temporal.py` | Sanjay | DONE |
| Config | `config.py` | Shared | DONE |

---

## File Ownership Policy

```
DO NOT casually edit (shared files):
    model.py  config.py  scripts/dataset.py
    scripts/joint_transforms.py  hospital_splits.json  e8_server.py

Sanjay owns:  crypto.py  e7_temporal.py
Mukesh owns:  e4_dpsgd.py  scripts/privacy_accounting.py
              scripts/privacy_utility_sweep.py
              scripts/cross_centre_evaluation.py
              scripts/multiseed_runner.py
              e9_breach_attack.py  e10_window_sweep.py
              e11_empirical_sweep.py  e12_unseen_hospital.py
              e13_multiseed.py  e14_scalability.py  e15_fault_robustness.py
```

---

## Branch Info

```
Branch  : mukesh/sdfl-completion
Commits : 37f3ad2  Final Reconciliation: E3-E15 synthesis
          3e3ae30  E15: Fault robustness (10 scenarios)
          e3283eb  E14: Scalability benchmark
          d0602d9  E13: Multi-seed robustness
          a230b70  E12: LOCO generalisation
          812ed6a  E11: Privacy-utility sweep
          b0bc20f  E10: Temporal window analysis
          ab5c1bf  E9b: Temporal ablation
```
