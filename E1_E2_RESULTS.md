### Experiment E1 - Baseline

**Model:** ResUNet++
**Loss Function:** DiceBCELoss
**Optimizer:** Adam, lr=1e-4
**Epochs:** 50
**Batch Size:** 8
**Image Size:** 256 x 256

**Training:**
- Final train_loss: 0.1526
- Final val_loss: 0.1284
- Best val_dice: 0.8356 (target was >= 0.80)
- Best val_iou: 0.7581
- Checkpoint: checkpoints/e1_best.pth

**Test Set Results:**
- Dice: 0.7937
- IoU: 0.7159
- Precision: 0.8590
- Recall: 0.8220

**Status:** Complete.

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

**Training (federated validation, weighted across clients):**
- Round 1: val_dice 0.5448
- Round 10: val_dice 0.8067
- Round 19 (best): val_dice 0.8571, val_iou 0.7713
- Round 20 (final): val_dice 0.8518, val_iou 0.7687
- All 20 rounds completed, 0 client failures
- Per-round checkpoints: checkpoints/e2_round_1.pth through e2_round_20.pth

**Test Set Results (Round 19 checkpoint):**
- Dice: 0.7712
- IoU: 0.6818
- Precision: 0.7791
- Recall: 0.8493

**Status:** Complete. 3 clients trained independently, FedAvg aggregated without error every round.
