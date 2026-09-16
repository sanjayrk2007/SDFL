### Experiment E1 - Baseline

**Model:** ResUNet++
**Loss Function:** DiceBCELoss
**Optimizer:** Adam, lr=1e-4
**Epochs:** 50
**Batch Size:** 8
**Image Size:** 256 x 256

**Training:**
- Best val_dice: 0.8599
- Checkpoint: checkpoints/e1_best.pth

**Test Set Results:**
- Dice: 0.8182
- IoU: 0.7402
- Precision: 0.8532
- Recall: 0.8492

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`.

### Experiment E2 - Federated Learning (FedAvg)

**Framework:** Flower (flwr) + Ray simulation backend
**Clients:** 3 (one per non-IID hospital split)
**Rounds:** 20
**Local epochs per round:** 3

**Best round:** 16
**Test Set Results (best round checkpoint):**
- Dice: 0.7791
- IoU: 0.6905
- Precision: 0.8181
- Recall: 0.8208

**Status:** Complete. Reproduced on `integration/sdfl-final-validation`. Checkpoint: checkpoints/e2_best.pth
