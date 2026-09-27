### Experiment E1 - Baseline

**Model:** ResUNet++
**Loss Function:** DiceBCELoss
**Optimizer:** Adam, lr=1e-4
**Epochs:** 50
**Batch Size:** 8
**Image Size:** 256 x 256

**Training (Reproduced Run):**
- Best val_dice: 0.8599
- Checkpoint: `checkpoints/e1_best.pth`

**Test Set Results (Reproduced Run):**
- Dice: 0.8182
- IoU: 0.7402
- Precision: 0.8532
- Recall: 0.8492

*Historical Initial Run (pre-integration): Final train_loss: 0.1526, final val_loss: 0.1284, best val_dice: 0.8356, Test Dice: 0.7937, IoU: 0.7159, Precision: 0.8590, Recall: 0.8220.*

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`.

---

### Experiment E2 - Federated Learning (FedAvg)

**Framework:** Flower (flwr) + Ray simulation backend
**Clients:** 3 (one per non-IID hospital split)
**Rounds:** 20
**Local epochs per round:** 3
**Aggregation:** FedAvg, all 3 clients sampled every round

**Per-hospital data:**
- Hospital 0 (small-biased): train=264, val=32
- Hospital 1 (medium-biased): train=263, val=33
- Hospital 2 (large+medium-biased): train=262, val=38

**Training & Test Set Results (Reproduced Run):**
- Best round: 16
- Test Dice: 0.7791
- Test IoU: 0.6905
- Precision: 0.8181
- Recall: 0.8208
- Checkpoint: `checkpoints/e2_best.pth`

*Historical Initial Run (pre-integration): Best round 19 (val_dice 0.8571, val_iou 0.7713), Test Dice: 0.7712, IoU: 0.6818, Precision: 0.7791, Recall: 0.8493.*

**Status:** Complete. 3 clients trained independently, FedAvg aggregated without error every round. Reproduced on `integration/sdfl-final-validation`.
