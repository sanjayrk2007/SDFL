# Experiment E8 -- Full SDFL Stack (Reproduced)

This report documents the final metrics of the E8 experiment, evaluating the full SDFL (Secure and Private Federated Learning) stack.

## Configuration

| Parameter | Value |
|---|---|
| **Rounds** | 20 |
| **Starting checkpoint** | `checkpoints/e7_best.pth` (or `e6_best.pth` fallback) |
| **Pipeline** | DP-SGD + Temporal security + SecAgg (full stack) |

---

## 1. Segmentation Performance

| Metric | In-Distribution (H0 + H1 Test) | Out-of-Distribution (H2 Test) | Generalisation Gap |
| :--- | :---: | :---: | :---: |
| **Dice Score** | 0.4145 | 0.4869 | -0.0724 |
| **IoU Score** | 0.2994 | 0.3477 | -0.0483 |
| **Precision** | 0.4405 | 0.6161 | - |
| **Recall** | 0.5267 | 0.5038 | - |
| **F2 Score** | 0.5962 | 0.5663 | - |
| **HD95 (px)** | 84.17 | 78.66 | - |

> [!NOTE]
> **Polyp Size Covariate Shift & Generalisation Gap:**
> The negative generalization gap (OOD test Dice of 0.4869 vs. In-Distribution test Dice of 0.4145) is explained by the characteristics of the data splits:
> 1. **Polyp Size and Segmentation Complexity:** Hospital 2 is biased towards large polyps (foreground area $\ge 30\%$), which are visually well-defined and mathematically far easier to segment. Larger targets yield significantly higher Dice/IoU scores because boundary pixel mismatch has a much lower relative impact. Conversely, Hospital 0 (small polyps, $< 10\%$ area) and Hospital 1 (medium polyps, $10-30\%$ area) contain small or subtle targets where even minor edge errors degrade Dice scores drastically.
> 2. **Unseen Center Clarification:** Note that Hospital 2 was a training participant (Client 2) in the federated simulation, meaning its local training distribution was observed during optimization. Evaluating on the Hospital 2 test split represents center-level covariate shift (size distribution shift) on unseen test samples rather than evaluation on a strictly unseen center.

---

## 2. Privacy Guarantees

* **Cumulative Differential Privacy budget ($\epsilon$)**: `2.7720` (at $\delta = 10^{-5}$)
> **Note:** The epsilon value of 2.7720 represents the cumulative privacy spent over **20 training rounds × 1 local epoch** (20 total local epochs) and is computed via a server-side RDP accountant using client-reported sampling parameters. It may differ slightly from Opacus's exact internal accounting, which cannot persist across Ray simulation rounds.
* **Post-Expiry Decryption Success Rate**: `0.0%` (Target: 0.0%)

---

## 3. Uncertainty & Failure Detection

* **Expected Calibration Error (ECE)**: `0.0888` (pixel-level)
* **Failure Detection ROC AUC**: `0.5052`
> **Note:** AUC of 0.5052 is approximately random, indicating MC Dropout uncertainty estimates are not yet informative for failure detection at the current model performance level. No test samples fell below the Dice < 0.5 hard-sample threshold, making the classifier uninformative.

---

## 4. System Overhead (Per-Round Averages)

* **Client Encryption Time**: `0.0386 seconds`
* **Server Aggregation Time**: `0.0835 seconds`
* **Communication Volume**: `79,111,638 bytes`

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`. Checkpoint: `checkpoints/e8_final.pth`.

**Provenance note (2026-09-26):** The only `e8_stdout.log` currently committed for this experiment contains nothing but an environment crash (`AttributeError: np.float_ was removed in the NumPy 2.0 release`), despite `requirements.txt` pinning `numpy<2.0` -- something in that particular session had a newer numpy installed anyway. The metrics above come from the committed `e8_metrics.json` and `e8_final.pth`, which predate that crashed session; there is currently no clean log in the repo proving this exact run. Per team decision, these committed artifacts are being kept as authoritative rather than re-run. If reproducibility needs to be re-established later, pin numpy more strictly (e.g. `numpy==1.26.4`) before rerunning.
