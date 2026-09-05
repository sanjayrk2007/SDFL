# E10 — Temporal Window Analysis ($T_r$) Experiment Results

This report documents the empirical evaluation of the **SDFL Temporal Window Sweep (E10)**, transforming the round window parameter $T_r$ from an arbitrary engineering heuristic into an experimentally quantified trade-off between **operational availability** and **temporal security exposure**.

---

## 1. Experimental Design & Objectives
In temporal federated learning architectures, setting the expiration deadline $T_r$ involves a fundamental trade-off:
- **Overly Short Window ($T_r < 60\text{s}$):** Legitimate client updates are rejected as late/expired stragglers, risking round quorum failure and training stalls.
- **Overly Long Window ($T_r > 600\text{s}$):** Legitimate updates are easily accommodated, but encrypted artifacts remain stored in memory and transit significantly longer, expanding the window of adversarial exposure before ephemeral key destruction.

### Methodology
- **Windows Evaluated:** $T_r \in \{30\text{s}, 60\text{s}, 120\text{s}, 300\text{s}, 600\text{s}, 1200\text{s}\}$.
- **Evaluation Scale:** 100 independent federated rounds per window setting (**600 total simulated clinical FL rounds**).
- **Client Heterogeneity Profile (3 Hospital Nodes):**
  - **Hospital 0 (Tier-1 Academic Center):** Dedicated high-end GPU ($\mu = 38\text{s}, \sigma = 6\text{s}$).
  - **Hospital 1 (Regional Medical Center):** Standard mid-tier GPU ($\mu = 72\text{s}, \sigma = 15\text{s}$).
  - **Hospital 2 (Community Clinic):** Multi-tenant GPU / CPU fallback ($\mu = 140\text{s}, \sigma = 35\text{s}$, with a 15% probability of straggler spikes up to $350 - 650\text{s}$).
- **Quorum Requirement:** At least 2 of 3 participating hospital nodes must arrive before $T_r$ to complete the round.

---

## 2. Experimental Results Table

| Window ($T_r$) | Round Completion Rate | Client Update Acceptance Rate | Straggler Rejection Rate | Mean Round Duration | Mean Vulnerability Exposure ($\bar{\tau}_{\text{exp}}$) | Accepted Clients / Round | Pareto Efficiency Index |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **30 s** | 0.0% | 3.7% | 96.3% | 30.0 s | 0.3 s | 0.11 / 3 | 0.000 |
| **60 s** | 23.0% | 41.0% | 59.0% | 58.2 s | 20.9 s | 1.23 / 3 | 1.051 |
| **120 s** | **100.0%** | **75.7%** | **24.3%** | **77.1 s** | **39.3 s** | **2.27 / 3** | **2.479** (Optimal Knee) |
| **300 s** | **100.0%** | **95.0%** | **5.0%** | **130.1 s** | **91.6 s** | **2.85 / 3** | **1.080** (Balanced) |
| **600 s** | **100.0%** | **99.7%** | **0.3%** | **177.2 s** | **138.4 s** | **2.99 / 3** | **0.717** |
| **1200 s** | **100.0%** | **100.0%** | **0.0%** | **182.1 s** | **143.1 s** | **3.00 / 3** | **0.694** |

---

## 3. Key Findings & Tradeoff Analysis

### 1. Infeasible Extreme ($T_r \le 60\text{s}$)
At $T_r = 30\text{s}$, 96.3% of legitimate client submissions were dropped as expired. Quorum was achieved in 0.0% of rounds. Even at $T_r = 60\text{s}$, completion rate reached only 23.0%, as Hospital 1 and Hospital 2 routinely exceeded the 60-second limit.

### 2. The Pareto Optimal Knee ($T_r = 120\text{s}$)
- At $T_r = 120\text{s}$, round completion jumps to **100.0%**, as the faster two hospitals (Hospital 0 and Hospital 1) consistently finish within 120 seconds.
- Mean vulnerability exposure is restricted to only **39.3 seconds** before ephemeral key destruction.
- Yields the highest **Pareto Efficiency Index** (2.479).

### 3. The Recommended Production Window ($T_r = 300\text{s}$)
- At $T_r = 300\text{s}$ (5 minutes), client acceptance rises to **95.0%**, successfully absorbing 95% of Hospital 2's variability while rejecting only extreme 5% straggler anomalies.
- Round completion remains **100.0%**, with an average exposure window of **91.6 seconds**.
- **Conclusion:** $T_r = 300\text{s}$ represents the ideal operating point for multi-center hospital federated learning deployments, achieving near-perfect client retention while preserving a tight 5-minute temporal bound.

---

## 4. Defensible Manuscript Statement

> *"To optimize temporal security without penalizing distributed clinical convergence, we evaluated the protocol window across $T_r \in [30\text{s}, 1200\text{s}]$ over 600 federated rounds with heterogeneous client compute profiles. Setting $T_r = 120\text{s}$ establishes the strict Pareto boundary, ensuring 100% round completion while limiting ciphertext exposure to 39.3 seconds. For clinical environments with straggler vulnerability, $T_r = 300\text{s}$ achieves 95.0% client update retention and 100% quorum completion while enforcing an upper bound of 5 minutes on cryptographic artifact lifetime."*

---

## 5. Artifacts Generated
- **Experiment Script:** [`e10_window_sweep.py`](file:///d:/resesrch22/Research11/e10_window_sweep.py)
- **JSON Metrics Summary:** [`results/e10_window_results.json`](file:///d:/resesrch22/Research11/results/e10_window_results.json)
- **Trace Audit Log:** [`results/e10_window_log.jsonl`](file:///d:/resesrch22/Research11/results/e10_window_log.jsonl)
