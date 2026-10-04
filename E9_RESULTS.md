# E9 — Retrospective Breach Attack Evaluation

> Completed on branch: `mukesh/sdfl-completion`
> Entry-point: `e9_breach_attack.py`

---

## Protocol

This experiment evaluates the cryptographic security of the SDFL forward-secrecy mechanism against five attack conditions. All attacks are conducted strictly **post-expiry** ($t > T_r$), after `destroy_round_key()` has been called and the ephemeral AES-GCM round key is irreversibly zeroed from memory.

| Parameter | Value |
|-----------|-------|
| Trials per condition | 1,000 |
| Total attack attempts | 5,000 (5 conditions × 1,000) |
| Threat model | Retrospective post-breach adversary ($A_{\text{retro}}$) |
| Test weights | Synthetic float32 arrays $(16, 8, 3, 3)$ and $(16,)$ |
| Ciphertext | AES-256-GCM with canonical AAD binding |

> **Disclosure:** Weights are synthetic tensors, not live ResUNet++ gradients. The experiment tests the SDFL *cryptographic protocol implementation*, not the harder problem of gradient-inversion attacks against the aggregator's post-round plaintext model. A5 uses a linear noisy-vector proxy as a worst-case reconstruction candidate rather than a full iterative gradient-inversion optimizer.

---

## Attack Conditions & Results

| Condition | Attack Vector | Successes | Success Rate | 95% Upper Bound (Clopper-Pearson) |
|-----------|---------------|-----------|-------------|-----------------------------------|
| **A1** — Post-Expiry Direct Decryption | Attempt `decrypt_update()` with zeroed key (all zeros) | 0/1,000 | **0.0%** | < 0.3% |
| **A2** — Random Key Brute-Force | Guess random 256-bit key per trial | 0/1,000 | **0.0%** | < 0.3% |
| **A3** — Cross-Round Substitution | Inject stale ciphertext from different round context | 0/1,000 | **0.0%** | < 0.3% |
| **A4** — Certificate Tampering | Forge extended expiry in HMAC-signed certificate | 0/1,000 | **0.0%** | < 0.3% |
| **A5** — Plaintext Reconstruction Proxy | Reconstruct via linear combination of other clients + DP noise | 0/1,000 | **0.0%** | < 0.3% |

**Total: 0 / 5,000 successful breaches across all conditions.**

---

## Statistical Interpretation

- **Per-condition upper bound:** 0.3% (1-sided Clopper-Pearson, 95% confidence, $k=0$, $n=1000$)
- **Reported bound:** 0.3% per attack condition. The five conditions are **not pooled** into a single 0.06% figure, because they test distinct adversarial assumptions.
- AES-256-GCM with a destroyed round key provides 256-bit key-space security ($2^{256}$ guesses for A1/A2), a guarantee that far exceeds the 0/1,000 empirical test window.

---

## Interpretation

SDFL's forward-secrecy mechanism successfully prevents retrospective recovery of encrypted client model updates across all five attack conditions. The result is consistent with the information-theoretic guarantee of AES-256-GCM: after `destroy_round_key()` executes, the ciphertext is computationally irreversible regardless of adversarial artifacts (certificates, nonces, audit logs, transaction UIDs) that remain available.

---

## Limitations

1. Attacks use **synthetic tensors**, not recovered real gradients — the threat model is cryptographic breach, not gradient inversion.
2. **A5** is a linear proxy reconstruction. Full iterative gradient-inversion optimizers (e.g., iDLG, R-GAP) were not implemented; they require the plaintext model, which is unavailable post-key-destruction.
3. The adversary is assumed to have **post-expiry access** only; in-window active adversaries with valid credentials are outside the E9 threat model (addressed by E7 temporal and E9b ablation).
