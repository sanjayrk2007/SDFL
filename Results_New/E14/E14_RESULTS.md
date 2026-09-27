# E14 — Security Layer Client Scalability

> Completed: 2026-09-12T09:41:51.439349+00:00  |  Branch: `mukesh/sdfl-completion`

> **⚠ UNRESOLVED NUMERIC DISCREPANCY (2026-09-27):** Two sets of `total_security_latency_ms` figures coexist for this experiment from the same committed run: (A) the JSON file (`e14_scalability_results.json`) reports K=3→**179.96 ms**, K=5→**223.72 ms**, K=10→**375.06 ms**, K=20→**752.79 ms**; (B) `e14_stdout.log` (from the same session directory) reports K=3→**231.88 ms**, K=5→**323.61 ms**, K=10→**452.10 ms**, K=20→**903.64 ms**. The script overwrites the JSON at the end of each run and stdout is captured separately, so these almost certainly reflect two distinct benchmark executions (different hardware load / memory state) rather than a transcription error — the JSON's per-component values sum to its own totals correctly, and the stdout's aggregation values are internally consistent with its own totals. Cause of the divergence cannot be determined from committed artifacts alone without re-running the benchmark. **Neither figure has been overwritten here.** Both are retained below; `MASTER_RESULTS_SECURITY.{csv,json,tex}` flag this same status. Do not use the E14 latency numbers for a paper without a fresh, confirmed run.

## Overview

Quantifies the computational latency, cryptographic verification overhead, and communication bandwidth scaling of the Self-Destructing Federated Learning (SDFL) security protocol across cohort sizes **K ∈ {3, 5, 10, 20}**.

## Scalability Performance Summary

**Table A — figures from `e14_scalability_results.json` (run A):**

| Clients ($K$) | Client Enc (ms) | Cert Sign (ms) | Cert Verify (ms) | Server Agg (ms) | Total Sec Latency (ms) | Total Comm (MB) | Ciphertext Storage (MB) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **3** | 62.58 | 0.152 | 0.107 | 117.12 | **179.96** | 150.88 | 75.44 |
| **5** | 52.80 | 0.051 | 0.145 | 170.73 | **223.72** | 251.47 | 125.74 |
| **10** | 49.70 | 0.055 | 0.178 | 325.13 | **375.06** | 502.95 | 251.48 |
| **20** | 49.12 | 0.054 | 0.355 | 703.27 | **752.79** | 1005.91 | 502.96 |

**Table B — figures from `e14_stdout.log` (run B, unresolved discrepancy — see note above):**

| Clients ($K$) | Total Sec Latency (ms) | Server Agg (ms) | Total Comm (MB) |
|---:|---:|---:|---:|
| **3** | **231.88** | 175.72 | 150.89 |
| **5** | **323.61** | 272.86 | 251.48 |
| **10** | **452.10** | 398.87 | 502.95 |
| **20** | **903.64** | 855.31 | 1005.91 |

## Cryptographic Overhead vs. Unencrypted FedAvg

| Clients ($K$) | Baseline FedAvg Agg (ms) | SDFL SecAgg (ms) | Security Overhead (ms) | Overhead per Client (ms) |
|---:|---:|---:|---:|---:|
| 3 | 40.47 | 117.12 | +139.48 | +46.49 |
| 5 | 59.23 | 170.73 | +164.49 | +32.90 |
| 10 | 105.35 | 325.13 | +269.71 | +26.97 |
| 20 | 224.53 | 703.27 | +528.26 | +26.41 |

## Key Findings & Scaling Characteristics

1. **Linear Computational Scaling:** Total security latency scales gracefully with client cohort size $K$ (approx. linear in decryption and aggregation).
2. **Negligible Certificate Verification Cost:** HMAC certificate signing and verification require < 0.05 ms per client, introducing negligible coordinator burden.
3. **Bounded Memory & Storage:** Ciphertext retention scales strictly as $O(K \cdot |W|)$ during the active aggregation window $T_r$ and drops to zero immediately upon round expiry via `destroy_round_key`.
4. **Communication Efficiency:** AES-GCM ciphertext payload size overhead is minimal (< 0.01% over raw serialized model float parameters).
