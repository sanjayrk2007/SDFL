# E10 — Temporal Window Analysis ($T_r$) Experiment Results

This report documents the empirical evaluation of the **SDFL Temporal Window Sweep (E10)**, analyzing the operational availability versus security exposure trade-off across window durations $T_r \in [30\text{s}, 1200\text{s}]$.

---

## 1. Experimental Methodology & Simulation Assumptions
In temporal federated learning architectures, setting the expiration deadline $T_r$ involves a fundamental trade-off:
- **Short Window ($T_r \le 60\text{s}$):** Strengthens temporal privacy by bounding ciphertext lifetime, but risks dropping legitimate client updates as late stragglers.
- **Long Window ($T_r \ge 600\text{s}$):** Maximize client participation, but expands the window during which encrypted updates remain usable before key destruction.

### Simulation Assumptions (Heterogeneous Clinical Hardware Model)
To evaluate this trade-off realistically, client latencies were modeled based on parameterized distributions representing heterogeneous hospital hardware:
- **Hospital 0 (Tier-1 Academic Hospital):** High-end GPU workstation ($\mu = 38\text{s}, \sigma = 6\text{s}$, bounded $\ge 22\text{s}$).
- **Hospital 1 (Regional Medical Center):** Mid-tier GPU ($\mu = 72\text{s}, \sigma = 15\text{s}$, bounded $\ge 38\text{s}$).
- **Hospital 2 (Community Clinic):** Constrained GPU / CPU fallback ($\mu = 140\text{s}, \sigma = 35\text{s}$, with a 15% probability of straggler spikes between $320\text{s} - 650\text{s}$).

*Note: These latency distributions are parameterized simulation models designed to reflect clinical hardware diversity, rather than live physical hospital deployments.*

### Evaluation Scale
- Evaluated $T_r \in \{30\text{s}, 60\text{s}, 120\text{s}, 300\text{s}, 600\text{s}, 1200\text{s}\}$.
- 100 independent rounds per setting (**600 total simulated federated rounds**).
- **Quorum Criterion:** At least 2 of 3 hospital updates must arrive before $T_r$ to complete aggregation.

---

## 2. Authoritative Experimental Results Table

All metrics below are drawn directly from [`results/e10_window_results.json`](file:///d:/resesrch22/Research11/results/e10_window_results.json):

| Window ($T_r$) | Round Completion Rate | Client Update Acceptance Rate | Straggler Rejection Rate | Mean Round Duration | Mean Vulnerability Exposure ($\bar{\tau}_{\text{exp}}$) | Accepted Clients / Round |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **30 s** | 0.0% | 3.7% | 96.3% | 30.0 s | 0.3 s | 0.11 / 3 |
| **60 s** | 23.0% | 41.0% | 59.0% | 58.2 s | 20.9 s | 1.23 / 3 |
| **120 s** | **100.0%** | **75.7%** | **24.3%** | **77.1 s** | **39.3 s** | **2.27 / 3** |
| **300 s** | **100.0%** | **95.0%** | **5.0%** | **130.1 s** | **91.6 s** | **2.85 / 3** |
| **600 s** | **100.0%** | **99.7%** | **0.3%** | **177.2 s** | **138.4 s** | **2.99 / 3** |
| **1200 s** | **100.0%** | **100.0%** | **0.0%** | **182.1 s** | **143.1 s** | **3.00 / 3** |

---

## 3. Concrete Engineering Conclusions

1. **Infeasible Regime ($T_r \le 60\text{s}$):**
   - At $T_r = 30\text{s}$, legitimate updates are rejected 96.3% of the time, resulting in 0.0% round completion.
   - At $T_r = 60\text{s}$, completion rate reaches only 23.0%, as regional and community clinic nodes routinely require $> 60\text{s}$.
2. **Minimum Window for 100% Completion ($T_r = 120\text{s}$):**
   - $T_r = 120\text{s}$ is the minimum tested window achieving **100.0% round completion** (satisfying the 2-of-3 quorum requirement in all 100 rounds).
   - Limits average ciphertext vulnerability exposure to **39.3 seconds** before key destruction.
3. **Recommended Production Operating Point ($T_r = 300\text{s}$):**
   - $T_r = 300\text{s}$ (5 minutes) provides an operationally conservative setting, achieving **95.0% client update acceptance** across hardware variations while rejecting severe straggler spikes.
   - Preserves 100% round completion with a bounded mean exposure window of **91.6 seconds**.

---

## 4. Defensible Manuscript Statement

> *"In E10, we evaluated the effect of the temporal expiry window $T_r \in [30\text{s}, 1200\text{s}]$ across 600 simulated federated rounds modeling heterogeneous clinical compute and network distributions. Very short windows ($T_r \le 60\text{s}$) caused excessive legitimate update rejections (59.0%–96.3%) and round aborts. We found that $T_r = 120\text{s}$ is the minimum tested window achieving 100% round completion (with a mean vulnerability exposure of 39.3 seconds), while $T_r = 300\text{s}$ provides a practical operational setting achieving 95.0% client update retention and bounded exposure. E10 thus establishes the quantitative trade-off between operational availability and temporal security lifetime."*

---

## 5. Artifacts Generated
- **Experiment Script:** [`e10_window_sweep.py`](file:///d:/resesrch22/Research11/e10_window_sweep.py)
- **Authoritative JSON:** [`results/e10_window_results.json`](file:///d:/resesrch22/Research11/results/e10_window_results.json)
- **Round Trace Log:** [`results/e10_window_log.jsonl`](file:///d:/resesrch22/Research11/results/e10_window_log.jsonl)
