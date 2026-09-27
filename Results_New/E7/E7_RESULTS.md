# Experiment E7 -- Temporal Security Protocol (Reproduced)

## Configuration

| Parameter | Value |
|---|---|
| **Model** | ResUNet++ with GroupNorm and non-inplace ReLU |
| **Framework** | Flower (flwr) + Ray simulation backend + Opacus DP-SGD |
| **Clients** | 3 (one per non-IID hospital split) |
| **Rounds** | 1 (verification run) / 3 (simulation run) |
| **Local epochs per round** | 1 |
| **Proximal term μ** | 0.001 |
| **Clipping Norm (C)** | 2.0 |
| **Noise Multiplier (σ)** | 1.5 |
| **Symmetric Encryption** | AES-GCM (256-bit key) with mutable bytearray key destruction |
| **Temporal Expiry Window ($T_r$)** | 7200 seconds (2 hours) to support CPU training |
| **Signing Secret Key** | HMAC-SHA256 with 32-byte coordinator secret key |

---

## E7 Security Verification Tests

All 5 core security verification tests (16 test assertions total) passed successfully:

1. **Test 1 (Timely Submission):** Submit update at $T_r - 1\text{s}$ → accepted by aggregator.
2. **Test 2 (Expired Submission):** Submit update at $T_r + 1\text{s}$ → rejected with `expired` reason.
3. **Test 3 (Context Mismatch):** Submit update with invalid/mismatched `key_context_id` → rejected with `mismatch` reason.
4. **Test 4 (In-Memory Key Destruction):** Post-destruction key usage → raises `cryptography.exceptions.InvalidTag`.
5. **Test 5 (Audit Log Integrity):** Validated that `audit_log.jsonl` successfully records all 3 event types (`round_open`, `round_close`, `key_destroyed`).

### Verification Test Suite Summary
- Hash Tests A, B, C, D: Deterministic, data-sensitive, dtype-sensitive, shape-sensitive model hashing.
- Tests E & F: Certificate generation and client/update binding.
- Tests G, I, J, K: Cryptographic rejection of invalid signatures, wrong model hashes, mismatched client IDs, and replay attacks.
- Tests L & M: AAD validation preventing ciphertext modification or context switching.
- Test N: State cleanup and cached ciphertext purging post-round.

**Summary:** 16 passed, 0 failed.

---

## Historical Verification Simulation Results (3 Rounds)

| Round | val_loss | val_dice | val_iou | Checkpoint Saved |
|---|---|---|---|---|
| **Round 1** | 0.4357 | 0.5342 | 0.4018 | |
| **Round 2** | 0.4332 | 0.5323 | 0.4010 | |
| **Round 3** | 0.4344 | 0.5338 | 0.4020 | `checkpoints/e7_best.pth` |

---

## Verification Log Analysis

During the federated learning simulation, the temporal audit events are correctly appended to `audit_log.jsonl`:
- **Round Start:** Coordinates round ID, model hash, active participant IDs, and the dynamic expiry timestamp $T_r$. Logs `round_open`.
- **Round Completion (Success):** Server successfully aggregates client updates, wipes the ephemeral round key from memory in-place, clears cached ciphertexts, logs `round_close` and then `key_destroyed` with distinct timestamps.
- **Round Completion (Failure/Expiry):** If updates are late or invalid, strategy logs `round_expired_no_aggregation` instead of `round_close` and proceeds to destroy the key.

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`.
