import torch
import torch.nn as nn


class DiceBCELoss(nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, pred, target):
        numerator = 2 * (pred * target).sum() + 1
        denominator = pred.sum() + target.sum() + 1
        dice_loss = 1 - (numerator / denominator)

        bce_loss = nn.BCELoss()(pred, target)

        return 0.5 * dice_loss + 0.5 * bce_loss


if __name__ == "__main__":
    pred = torch.rand(2, 1, 256, 256)
    target = torch.randint(0, 2, (2, 1, 256, 256)).float()
    loss_fn = DiceBCELoss()
    loss = loss_fn(pred, target)
    print(loss.item())
