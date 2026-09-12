"""
scripts/multiseed_runner.py
-----------------------------
Mukesh TASK 5 -- Multi-seed robustness runner.

Evaluates existing checkpoints across multiple random seeds and aggregates
Dice mean/std. Uses the same checkpoint-loading logic as E13.

Usage:
    python scripts/multiseed_runner.py [--seeds 42 43 44]
                                       [--checkpoints e2_round_20.pth e3_best.pth e11_best.pth]

Outputs:
    results/multiseed_results.json
    results/multiseed_results.csv
"""

import argparse
import csv
import json
import os
import random
import sys
import time

import numpy as np
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from e2_server import ResUNetPlusPlus, DEVICE, get_parameters, set_parameters  # noqa: E402

RESULTS_DIR  = os.path.join(ROOT, "results")
CKPT_DIR     = os.path.join(ROOT, "checkpoints")


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def dice_score(pred, target, eps=1e-6):
    pred  = (torch.sigmoid(pred) > 0.5).float()
    inter = (pred * target).sum()
    return float((2 * inter + eps) / (pred.sum() + target.sum() + eps))


def load_model_from_checkpoint(ckpt_path):
    sd = torch.load(ckpt_path, map_location=DEVICE, weights_only=False)
    if isinstance(sd, dict) and "model_state_dict" in sd:
        sd = sd["model_state_dict"]
    model = ResUNetPlusPlus(in_channels=3, out_channels=1).to(DEVICE)
    has_bn = any("running_mean" in k for k in sd.keys())
    if not has_bn:
        new_sd = {k.replace("_module.", ""): v for k, v in sd.items()}
        model.load_state_dict(new_sd, strict=False)
    else:
        model.load_state_dict(sd, strict=True)
    model.eval()
    return model


def evaluate_with_seed(model, seed, img_dir, mask_dir, n_samples=50):
    """Evaluate model on n_samples random images with given seed."""
    set_seed(seed)
    from scripts.dataset import KvasirSegDataset
    from scripts.joint_transforms import Compose, Resize, ToTensor

    tfm = Compose([Resize((256, 256)), ToTensor()])
    ds  = KvasirSegDataset(img_dir, mask_dir, transform=tfm)

    indices = random.sample(range(len(ds)), min(n_samples, len(ds)))
    scores  = []
    with torch.no_grad():
        for idx in indices:
            img, mask = ds[idx]
            img  = img.unsqueeze(0).to(DEVICE)
            mask = mask.unsqueeze(0).to(DEVICE)
            pred = model(img)
            scores.append(dice_score(pred, mask))
    return float(np.mean(scores)), float(np.std(scores))


def main():
    p = argparse.ArgumentParser(description="Multi-Seed Robustness Runner")
    p.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    p.add_argument("--checkpoints", type=str, nargs="+",
                   default=["e2_round_20.pth", "e3_best.pth", "e11_best.pth"])
    p.add_argument("--img-dir",  type=str,
                   default=os.path.join(ROOT, "data", "kvasir-seg", "images"))
    p.add_argument("--mask-dir", type=str,
                   default=os.path.join(ROOT, "data", "kvasir-seg", "masks"))
    p.add_argument("--n-samples", type=int, default=50,
                   help="Random samples per (checkpoint, seed) combo")
    args = p.parse_args()

    print(f"[multiseed] Seeds       : {args.seeds}")
    print(f"[multiseed] Checkpoints : {args.checkpoints}")
    print(f"[multiseed] n_samples   : {args.n_samples}")

    all_rows = []
    summary  = {}

    for ckpt_name in args.checkpoints:
        ckpt_path = os.path.join(CKPT_DIR, ckpt_name)
        if not os.path.exists(ckpt_path):
            print(f"[SKIP] {ckpt_path} not found")
            continue

        print(f"\n--- {ckpt_name} ---")
        model       = load_model_from_checkpoint(ckpt_path)
        seed_means  = []
        seed_stds   = []

        for seed in args.seeds:
            mean, std = evaluate_with_seed(model, seed, args.img_dir, args.mask_dir, args.n_samples)
            print(f"  seed={seed}  dice={mean:.4f} ± {std:.4f}")
            seed_means.append(mean)
            seed_stds.append(std)
            all_rows.append({
                "checkpoint": ckpt_name, "seed": seed,
                "dice_mean": mean, "dice_std": std,
            })

        agg_mean = float(np.mean(seed_means))
        agg_std  = float(np.std(seed_means))
        print(f"  -> Aggregate  {agg_mean:.4f} ± {agg_std:.4f}")
        summary[ckpt_name] = {"mean": agg_mean, "std": agg_std, "seed_means": seed_means}

    results = {"rows": all_rows, "summary": summary,
               "seeds": args.seeds, "checkpoints": args.checkpoints}

    os.makedirs(RESULTS_DIR, exist_ok=True)
    json_path = os.path.join(RESULTS_DIR, "multiseed_results.json")
    csv_path  = os.path.join(RESULTS_DIR, "multiseed_results.csv")

    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    if all_rows:
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            w.writeheader(); w.writerows(all_rows)

    print(f"\nSaved: {json_path}\nSaved: {csv_path}")


if __name__ == "__main__":
    main()
