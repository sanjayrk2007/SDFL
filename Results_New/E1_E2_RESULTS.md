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
