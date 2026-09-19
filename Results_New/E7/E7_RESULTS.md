# Experiment E7 -- Temporal Security Protocol (Reproduced)

## Configuration

| Parameter | Value |
|---|---|
| **Mode** | Verification tests only (--test_only) |

## Verification Test Results

Hash Test A passed.
Hash Test B passed.
Hash Test C passed.
Hash Test D passed.
Test E & F passed.
Test 1 passed: Timely submission accepted.
Test G passed: Invalid signature rejected.
Test 2 passed: Expired submission rejected.
Test I passed: Wrong model hash rejected.
Test J passed: Mismatched logical client ID rejected.
Test K passed: Replay rejected.
Test L & M passed: AAD mismatch raised InvalidTag during decryption.
Test 3 passed: Key context mismatch rejected.
Test 4 passed: Decryption with destroyed key raised InvalidTag.
Test N passed: Replay state and cached ciphertexts cleaned after round.
Test 5 passed: All 3 event types present in audit log.

**Summary:** 16 passed, 0 failed

## Full run log (tail)

```
[SECURITY WARNING] SDFL_HMAC_SECRET_KEY is not set — falling back to the insecure, publicly-committed development key. Set SDFL_HMAC_SECRET_KEY before running anything whose certificates/results are meant to be trusted (see SDFL_Preflight_Audit.md, Section 3).
=== Running E7 Temporal Security Verification Tests ===
Running Hash Test A: Deterministic repeated hashing...
Hash Test A passed.
Running Hash Test B: Different tensor values => different hash...
Hash Test B passed.
Running Hash Test C: Different dtype => different hash...
Hash Test C passed.
Running Hash Test D: Different shape => different hash...
Hash Test D passed.
Running Test E & F: Certificate contains client_id and update_hash...
Test E & F passed.
Running Test 1 (G): Timely submission & signature verification...
Test 1 passed: Timely submission accepted.
Running Test G: Certificate signature rejects modification...
Test G passed: Invalid signature rejected.
Running Test 2 (H): Submit update at Tr + 1s...
Test 2 passed: Expired submission rejected.
Running Test I: Wrong model hash rejected...
Test I passed: Wrong model hash rejected.
Running Test J: Mismatched client ID rejected...
Test J passed: Mismatched logical client ID rejected.
Running Test K: Duplicate update rejected...
Test K passed: Replay rejected.
Running Test L & M: Modified ciphertext and AAD mismatch decryption failure...
Test L & M passed: AAD mismatch raised InvalidTag during decryption.
Running Test 3: Submit update with wrong key_context_id...
Test 3 passed: Key context mismatch rejected.
Running Test 4: Post-expiry decryption attempt must fail...
Test 4 passed: Decryption with destroyed key raised InvalidTag.
Running Test N & Test 5: Full round aggregation and cleanup...
Test N passed: Replay state and cached ciphertexts cleaned after round.
Log events found: ['round_open', 'round_close', 'key_destroyed']
Test 5 passed: All 3 event types present in audit log.
All E7 security verification tests passed successfully!
```

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`.
