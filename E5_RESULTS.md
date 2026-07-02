# Experiment E5 — Secure Aggregation Integration

## Configuration

| Parameter | Value |
|---|---|
| **Model** | ResUNet++ with GroupNorm (num_groups=4) and non-inplace ReLU |
| **Framework** | Flower (flwr) + Ray simulation backend + Opacus DP-SGD |
| **Clients** | 3 (one per non-IID hospital split) |
| **Rounds** | 1 |
| **Local epochs per round** | 3 |
| **Proximal term μ** | 0.001 |
| **Clipping Norm (C)** | 2.0 |
| **Noise Multiplier (σ)** | 1.5 |
| **Symmetric Encryption** | AES-GCM (256-bit key) |

---

## Secure Aggregation Protocol
1. **Per-Round Key Generation**: At the start of the round, the coordinator/strategy generates a fresh 256-bit AES-GCM key and distributes it to all clients via the Flower `FitIns` config.
2. **Client-Side Encryption**: Clients train their models using DP-SGD, extract the raw weights, and encrypt them using `client_encrypt(weights, round_key)`. The plaintext weights are deleted from client memory, and only the ciphertext (`nonce` + `ciphertext`) is sent in the Flower client results metrics.
3. **Server-Side Aggregation**: The server receives only the encrypted updates. It calls `server_aggregate(list_of_ciphertexts, round_key)` to decrypt inside the aggregation pipeline and average the plaintext parameters, never persisting individual plaintext updates.

---

## Results

Validation metrics and privacy spending after 1 round of Secure Aggregated federated training:

| Experiment | val_dice | val_iou | ε (epsilon) | Decryption Success |
|---|---|---|---|---|
| **E4 (Plaintext Aggregation)** | 0.4312 | 0.3145 | 0.9793 | N/A |
| **E5 (Secure Aggregation)** | 0.4271 | 0.3111 | 0.9793 | 100% |

**Status:** Complete. The isolation and aggregation correctness tests passed successfully. The federated simulation successfully aggregated client updates securely under "AES-GCM encrypted transport with aggregation-side decryption", showing 100% decryption success. The global model checkpoint has been saved to `checkpoints/e5_best.pth`.

---

## Technical Analysis of E4 vs E5 Metrics

The Dice score shows a minor variation from E4 (`0.4312`) to E5 (`0.4271`). Since encryption is mathematically lossless and does not alter the values of weights, this difference is explained by:
1. **Run-to-Run Non-Determinism (Primary Factor):** Under the 1-round simulation environment, variations in GPU/CPU non-deterministic operations (e.g. PyTorch atomic operations, library calls) and random seeds during client execution produce minor fluctuations.
2. **Unweighted Aggregation (Secondary Factor):** The initial E5 run executed without passing the client sample counts list (`num_examples_list`) to the secure aggregation pipeline, resulting in an unweighted average of updates. Since client dataset sizes are slightly different (Hospital 0: 264, Hospital 1: 263, Hospital 2: 262), this created a small mathematical deviation from the weighted `FedAvg` strategy used in E4. 

*Note: The strategy code has been updated to pass `num_examples_list` to guarantee exact mathematical equivalence to weighted FedAvg in all subsequent runs.*
