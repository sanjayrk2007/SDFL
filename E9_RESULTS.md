# E9 — Retrospective Breach Attack Experiment Results

This report documents the empirical evaluation of the **SDFL Retrospective Post-Breach Attack Experiment (E9)**, addressing the core security claim of temporal update invalidation for the journal paper.

---

## 1. Threat Model & Adversary Capabilities

### Adversary Profile: Retrospective Adversary ($\mathcal{A}_{\text{retro}}$)
- **Timing Boundary:** $\mathcal{A}_{\text{retro}}$ operates strictly *after* round completion and temporal expiry ($t > T_r$), following in-memory self-destruction of the ephemeral round key $K_r$.
- **Adversary Knowledge & Intercepted Artifacts:**
  1. Intercepted ciphertext: $C_r$
  2. Cryptographic nonce: $N_r$ (12 bytes)
  3. AES-GCM authentication tag: $\tau_r$ (16 bytes)
  4. Round certificate: $\text{Cert}_r = (r, H(M_r), P_r, KID_r, T_r)$
  5. Coordinator signature: $\sigma_r = \text{HMAC}_{K_{\text{coord}}}(\text{Cert}_r)$
  6. Transaction identifier: $UID_r$
  7. Associated Authenticated Data: $\text{AAD}_r = \text{JSON}(\text{Cert}_r, \sigma_r, UID_r)$
  8. Append-only audit log records: $\mathcal{L}$ (`round_open`, `round_close`, `key_destroyed`)
  9. Pre- and post-round public global model parameters: $M_{r-1}, M_r$
- **Explicitly Excluded from Threat Model (Out of Scope):**
  - The destroyed round key $K_r$ (zeroed in RAM via `destroy_round_key`).
  - Active runtime memory dumping during the valid round window ($t < T_r$).
  - A live decryption oracle or coordinator signing key.

---

## 2. Experimental Attack Matrix ($N = 1,000$ Trials per Condition)

We evaluated **5,000 independent attack attempts** (1,000 trials per attack condition). In each trial, fresh cryptographic keys, nonces, client update vectors, transaction UIDs, and signed certificates were generated to ensure statistical independence.

| Condition | Attack Description | Intercepted Artifacts Used | Target Mechanism Tested | Success Rate | Primary Failure Reason |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **A1** | **Zeroed-Key Memory Exploit** | $C_r, N_r, \text{AAD}_r, K_{\text{zeroed}}$ | In-memory key zeroization | **0 / 1,000** (0.00%) | `InvalidTag`: Zeroed key buffer tag mismatch |
| **A2** | **Random 256-bit Key Guessing** | $C_r, N_r, \text{AAD}_r, K_{\text{cand}} \sim \{0,1\}^{256}$ | AES-GCM 256-bit security | **0 / 1,000** (0.00%) | `InvalidTag`: Tag verification failed ($p \le 2^{-128}$) |
| **A3** | **Cross-Round Substitution** | $C_r, N_r, K_{r'}, \text{AAD}_{r'}$ | Ephemeral key & context isolation | **0 / 1,000** (0.00%) | `InvalidTag`: Round key isolation & AAD mismatch |
| **A4** | **Certificate Tampering & Replay** | $C_r, N_r, \text{Cert}_{\text{tampered}}, \sigma_r$ | Authenticated timestamp binding | **0 / 1,000** (0.00%) | `rejected`: `invalid_signature` & `InvalidTag` |
| **A5** | **Plaintext Reconstruction** | $C_r, N_r, \text{AAD}_r, M_{r-1}, M_r$ | Full stack cryptographic binding | **0 / 1,000** (0.00%) | `authentication_failed`: Tag validation failed |

---

## 3. Statistical Bound Analysis

When evaluating security against an adversary with $k = 0$ observed successes in $N$ independent Bernoulli trials:

1. **Rule of Three Approximation ($95\%$ Confidence Upper Bound):**
   $$p_{\text{upper}} \approx \frac{-\ln(0.05)}{N} = \frac{2.9957}{1,000} \approx 0.30\% \quad (\text{per condition})$$
   $$\text{Pooled across all conditions } (N=5,000): \quad p_{\text{upper}} \approx \frac{2.9957}{5,000} \approx 0.060\%$$

2. **Exact Clopper-Pearson 95% Confidence Interval ($k=0$):**
   $$\text{CI}_{95\%} = \left[0.0000,\, 1 - 0.05^{1/N}\right] = [0.00\%,\, 0.30\%] \quad (\text{for } N = 1,000)$$

---

## 4. Defensible Journal Manuscript Statement

> *"Under the defined retrospective post-breach threat model, where an adversary acquires all retained transmission artifacts (ciphertext, nonce, certificate, signature, transaction UID, and audit log) after round expiry, zero successful plaintext recoveries were observed across 1,000 independent randomized attack attempts per primary attack condition (total $N = 5,000$ attack attempts; empirical breach success rate $= 0.00\%$, one-sided $95\%$ Clopper-Pearson upper bound $\le 0.30\%$). In-memory self-destruction and AES-GCM Associated Authenticated Data (AAD) context binding mathematically enforce that post-expiry updates cannot be recovered through the protocol."*

---

## 5. Artifacts Generated
- **Attack Script:** [`e9_breach_attack.py`](file:///d:/resesrch22/Research11/e9_breach_attack.py)
- **Detailed JSON Output:** [`results/e9_breach_results.json`](file:///d:/resesrch22/Research11/results/e9_breach_results.json)
- **Trace Audit Log:** [`results/e9_attack_log.jsonl`](file:///d:/resesrch22/Research11/results/e9_attack_log.jsonl)
