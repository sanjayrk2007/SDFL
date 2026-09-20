# Experiment E8 -- Full SDFL Stack (Reproduced)

## Configuration

| Parameter | Value |
|---|---|
| **Rounds** | 20 |
| **Starting checkpoint** | checkpoints/e7_best.pth (or e6_best.pth fallback) |
| **Pipeline** | DP-SGD + Temporal security + SecAgg (full stack) |

## Segmentation Performance

| Metric | In-Distribution | Out-of-Distribution |
|---|---:|---:|
| Dice | 0.4144991088070659 | 0.4868717767088581 |
| Iou | 0.29936811926533835 | 0.3476511542560355 |
| Precision | 0.44048215970449317 | 0.616131820016867 |
| Recall | 0.5267419275702757 | 0.5037981723318532 |

## Privacy, System & Uncertainty Metrics

| Metric | Value |
|---|---:|
| final_epsilon | 2.772045574725495 |
| delta | 1e-05 |
| post_expiry_decryption_success_rate | 0.0 |
| encryption_time_per_round | [0.055806239446004234, 0.029459317525227863, 0.03038962682088216] |
| aggregation_time_per_round | [0.09529995918273926, 0.07777881622314453, 0.07729721069335938] |
| communication_bytes_per_round | [79111638, 79111638, 79111638] |
| ece | 0.0888407084826281 |
| failure_detection_auc | 0.5051674245556015 |

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`.
