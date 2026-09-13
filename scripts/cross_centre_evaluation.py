"""
scripts/cross_centre_evaluation.py
------------------------------------
Mukesh TASK 4 -- True unseen-hospital (leave-one-client-out) evaluator.

Loads a trained checkpoint and evaluates it separately on each hospital split,
including one held-out split that had ZERO training samples.

Usage:
    python scripts/cross_centre_evaluation.py [--checkpoint PATH]
                                              [--unseen-hospital ID]
                                              [--rounds N]

Outputs:
    results/cross_centre_evaluation.json
"""

import argparse
import json
import os
import sys
import time

import torch
import torch.nn.functional as F

# Resolve repo root so imports work regardless of cwd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from e2_server import ResUNetPlusPlus, DEVICE, get_parameters, set_parameters  # noqa: E402

SPLITS_FILE = os.path.join(ROOT, "hospital_splits.json")
RESULTS_DIR = os.path.join(ROOT, "results")


def dice_score(pred, target, eps=1e-6):
    pred   = (torch.sigmoid(pred) > 0.5).float()
    inter  = (pred * target).sum()
    return float((2 * inter + eps) / (pred.sum() + target.sum() + eps))


def load_splits():
    with open(SPLITS_FILE) as f:
        data = json.load(f)
    return {int(k): v["filenames"] for k, v in data["hospitals"].items()}


def load_checkpoint(path):
    """Load checkpoint; handle BN vs GroupNorm (Opacus) architectures."""
    sd = torch.load(path, map_location=DEVICE, weights_only=False)
    if isinstance(sd, dict) and "model_state_dict" in sd:
        sd = sd["model_state_dict"]
    model = ResUNetPlusPlus(in_channels=3, out_channels=1).to(DEVICE)
    has_bn = any("running_mean" in k for k in sd.keys())
    if not has_bn:
        # Opacus GroupNorm: strip _module prefix if present
        new_sd = {}
        for k, v in sd.items():
            new_k = k.replace("_module.", "")
            new_sd[new_k] = v
        model.load_state_dict(new_sd, strict=False)
    else:
        model.load_state_dict(sd, strict=True)
    model.eval()
    return model


def evaluate_hospital(model, filenames, img_dir, mask_dir):
    """Evaluate model on a list of image filenames. Returns mean Dice."""
    from scripts.dataset import KvasirSegDataset
    from scripts.joint_transforms import Compose, Resize, ToTensor

    tfm = Compose([Resize((256, 256)), ToTensor()])
    ds  = KvasirSegDataset(img_dir, mask_dir, transform=tfm)
    stems_set = set(filenames)
    ds.stems = [s for s in ds.stems if s in stems_set]

    if len(ds) == 0:
        return None  # truly unseen; no eval samples

    loader = torch.utils.data.DataLoader(ds, batch_size=4, shuffle=False)
    scores = []
    with torch.no_grad():
        for imgs, masks in loader:
            imgs, masks = imgs.to(DEVICE), masks.to(DEVICE)
            preds = model(imgs)
            for i in range(preds.shape[0]):
                scores.append(dice_score(preds[i], masks[i]))
    return float(sum(scores) / len(scores)) if scores else 0.0


def main():
    p = argparse.ArgumentParser(description="Cross-Centre Evaluation")
    p.add_argument("--checkpoint", type=str,
                   default=os.path.join(ROOT, "checkpoints", "e3_best.pth"))
    p.add_argument("--unseen-hospital", type=int, default=2,
                   help="Hospital ID held out during training")
    p.add_argument("--img-dir",  type=str,
                   default=os.path.join(ROOT, "data", "kvasir-seg", "images"))
    p.add_argument("--mask-dir", type=str,
                   default=os.path.join(ROOT, "data", "kvasir-seg", "masks"))
    args = p.parse_args()

    print(f"[cross_centre] Checkpoint : {args.checkpoint}")
    print(f"[cross_centre] Unseen     : Hospital {args.unseen_hospital}")

    splits = load_splits()
    model  = load_checkpoint(args.checkpoint)

    results = {"checkpoint": args.checkpoint, "hospitals": {}, "summary": {}}
    dices   = []

    for hid, filenames in sorted(splits.items()):
        label = "UNSEEN (0 training samples)" if hid == args.unseen_hospital else f"Seen ({len(filenames)} files)"
        print(f"  H{hid} [{label}] evaluating {len(filenames)} files ...")
        dice = evaluate_hospital(model, filenames, args.img_dir, args.mask_dir)
        results["hospitals"][hid] = {
            "filenames_count": len(filenames),
            "unseen": hid == args.unseen_hospital,
            "dice": dice,
        }
        if dice is not None:
            dices.append(dice)
        print(f"  H{hid} Dice = {dice:.4f}" if dice is not None else f"  H{hid} Dice = N/A")

    macro_mean = float(sum(dices) / len(dices)) if dices else 0.0
    seen_dices = [v["dice"] for k, v in results["hospitals"].items()
                  if not v["unseen"] and v["dice"] is not None]
    seen_mean  = float(sum(seen_dices) / len(seen_dices)) if seen_dices else 0.0
    unseen_dice = results["hospitals"].get(args.unseen_hospital, {}).get("dice")
    gap = (seen_mean - unseen_dice) if unseen_dice is not None else None

    results["summary"] = {
        "macro_mean_dice": macro_mean,
        "seen_mean_dice":  seen_mean,
        "unseen_dice":     unseen_dice,
        "generalisation_gap": gap,
        "num_hospitals": len(splits),
        "unseen_hospital_id": args.unseen_hospital,
    }

    print(f"\n[SUMMARY] Macro Mean Dice : {macro_mean:.4f}")
    print(f"[SUMMARY] Seen  Mean Dice : {seen_mean:.4f}")
    print(f"[SUMMARY] Unseen Dice     : {unseen_dice}")
    print(f"[SUMMARY] Gap             : {gap}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    out_path = os.path.join(RESULTS_DIR, "cross_centre_evaluation.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
