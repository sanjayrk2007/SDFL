# E8 — Full SDFL Stack Experiment Results

This report documents the final metrics of the E8 experiment, evaluating the full SDFL (Secure and Private Federated Learning) stack.

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
> The negative generalization gap (where OOD performance exceeds in-distribution performance) is due to the larger, well-defined polyps contained in the Hospital 2 cohort compared to the smaller, more challenging cases in Hospitals 0 and 1.

## 2. Privacy Guarantees

* **Cumulative Differential Privacy budget (ε)**: `2.7720` (at $\delta = 1e-05$)
* **Post-Expiry Decryption Success Rate**: `0.0%` (Target: 0.0%)

## 3. Uncertainty & Failure Detection

* **Expected Calibration Error (ECE)**: `0.0888` (pixel-level)
* **Failure Detection ROC AUC**: `0.5052`

## 4. System Overhead (Per-Round Averages)

* **Client Encryption Time**: `0.0386 seconds`
* **Server Aggregation Time**: `0.0835 seconds`
* **Communication Volume**: `79,111,638 bytes`
