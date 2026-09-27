# Experiment E7 — Temporal Key Destruction

## Configuration

| Parameter | Value |
|---|---|
| **Model** | ResUNet++ with GroupNorm and non-inplace ReLU |
| **Framework** | Flower (flwr) + Ray simulation backend + Opacus DP-SGD |
| **Clients** | 3 (one per non-IID hospital split) |
| **Rounds** | 1 (verification run) |
| **Local epochs per round** | 1 |
| **Proximal term μ** | 0.001 |
| **Clipping Norm (C)** | 2.0 |
| **Noise Multiplier (σ)** | 1.5 |
| **Symmetric Encryption** | AES-GCM (256-bit key) with mutable bytearray key destruction |
| **Temporal Expiry Window (Tr)** | 7200 seconds (2 hours) to support CPU training |
| **Signing Secret Key** | HMAC-SHA256 with 32-byte coordinator secret key |

---

## E7 Security Verification Tests

All 5 required security verification tests passed successfully before simulation:

1. **Test 1 (Timely Submission):** Submit update at `Tr - 1s` &rarr; accepted by aggregator.
2. **Test 2 (Expired Submission):** Submit update at `Tr + 1s` &rarr; rejected with `expired` reason.
3. **Test 3 (Context Mismatch):** Submit update with invalid/mismatched `key_context_id` &rarr; rejected with `mismatch` reason.
4. **Test 4 (In-Memory Key Destruction):** Post-destruction key usage &rarr; raises `cryptography.exceptions.InvalidTag`.
5. **Test 5 (Audit Log Integrity):** Validated that `audit_log.jsonl` successfully records all 3 event types (`round_open`, `round_close`, `key_destroyed`).

---

## Results

Validation metrics from the E7 verification simulation (3 rounds):

| Round | val_loss | val_dice | val_iou | Checkpoint Saved |
|---|---|---|---|---|
| **Round 1** | 0.4357 | 0.5342 | 0.4018 | |
| **Round 2** | 0.4332 | 0.5323 | 0.4010 | |
| **Round 3** | 0.4344 | 0.5338 | 0.4020 | `checkpoints/e7_best.pth` |

---

## Verification Log Analysis

During the federated learning simulation, the temporal audit events were correctly appended to `audit_log.jsonl`:
- **Round Start:** Coordinates round ID, model hash, active participant IDs, and the dynamic expiry timestamp `Tr`. Logs `round_open`.
- **Round Completion (Success):** Server successfully aggregates client updates, wipes the ephemeral round key from memory in-place, clears cached ciphertexts, logs `round_close` and then `key_destroyed` with distinct timestamps.
- **Round Completion (Failure/Expiry):** If updates are late or invalid, strategy logs `round_expired_no_aggregation` instead of `round_close` and proceeds to destroy the key.
