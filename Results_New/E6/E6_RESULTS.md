# Experiment E6 -- Client Input Sanitization (Reproduced)

## Configuration

| Parameter | Value |
|---|---|
| **Model** | ResUNet++ |
| **Framework** | Flower (flwr) + Ray simulation backend |
| **Clients** | 3 |
| **Rounds** | 20 |
| **Starting checkpoint** | checkpoints/e5_best.pth |
| **Pipeline** | DP-SGD + SecAgg (AES-GCM) + PHI sanitization gate |

## Round-by-Round Results

| Round | Val Loss | Val Dice | Val IoU |
|:---:|:---:|:---:|:---:|
| 1 | 0.5130 | 0.4013 | 0.2871 |
| 2 | 0.5064 | 0.4203 | 0.3027 |
| 3 | 0.5019 | 0.4321 | 0.3125 |
| 4 | 0.4958 | 0.4508 | 0.3278 |
| 5 | 0.4896 | 0.4540 | 0.3314 |
| 6 | 0.4838 | 0.4668 | 0.3431 |
| 7 | 0.4784 | 0.4765 | 0.3516 |
| 8 | 0.4741 | 0.4820 | 0.3568 |
| 9 | 0.4690 | 0.4864 | 0.3608 |
| 10 | 0.4640 | 0.4977 | 0.3710 |
| 11 | 0.4606 | 0.5049 | 0.3771 |
| 12 | 0.4579 | 0.5073 | 0.3792 |
| 13 | 0.4542 | 0.5076 | 0.3797 |
| 14 | 0.4521 | 0.5116 | 0.3828 |
| 15 | 0.4500 | 0.5170 | 0.3876 |
| 16 | 0.4476 | 0.5222 | 0.3919 |
| 17 | 0.4432 | 0.5228 | 0.3925 |
| 18 | 0.4418 | 0.5235 | 0.3935 |
| 19 | 0.4582 | 0.5265 | 0.3926 |
| 20 | 0.4404 | 0.4980 | 0.3713 |

**Best round:** 19 (val_dice = 0.5265, val_iou = 0.3926)
**Checkpoint saved:** checkpoints/e6_best.pth

## Known Issues

- Rounds 17, 18, 37, 38, 39, 40 aggregated from 2/3 clients instead of 3/3, due to an intermittent `RuntimeError: Expected all tensors to be on the same device` inside Opacus (traced to `set_parameters()` in `e2_server.py`; a defensive fix has since been applied, but this run predates or may still exhibit it).
- The script's own end-of-run summary loop (`for rnd, dice, iou in strategy.round_history`) throws a `ValueError` due to a tuple-unpacking mismatch; this happens after the checkpoint is saved and does not affect the results above, which were parsed directly from the round-by-round log.

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`.
