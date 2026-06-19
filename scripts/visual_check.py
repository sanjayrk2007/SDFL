"""
SDFL — Visual sanity check
Owner: Sameer (Step 1b)

Saves N augmented (image, mask) pairs as side-by-side PNGs so you can
eyeball that the mask stays aligned with the image after every transform
in the pipeline (flip/rotate/crop/elastic). Required self-test before
handoff per the task spec.

Run:
    python scripts/visual_check.py --n 5

Output: outputs/sanity_check_{i}.png  (image | mask | overlay, 3 panels)
"""

import os
import sys
import argparse

import numpy as np
import torch
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from dataset import KvasirSegDataset


def unnormalize(img_tensor, mean, std):
    mean = torch.tensor(mean).view(3, 1, 1)
    std = torch.tensor(std).view(3, 1, 1)
    return (img_tensor * std + mean).clamp(0, 1)


def tensor_to_pil(img_tensor):
    arr = (img_tensor.permute(1, 2, 0).numpy() * 255).astype(np.uint8)
    return Image.fromarray(arr)


def mask_tensor_to_pil(mask_tensor):
    arr = (mask_tensor.squeeze(0).numpy() * 255).astype(np.uint8)
    return Image.fromarray(arr, mode="L")


def make_overlay(img_pil, mask_pil, color=(255, 0, 0), alpha=0.45):
    img_rgba = img_pil.convert("RGBA")
    mask_arr = np.array(mask_pil)
    overlay_arr = np.zeros((*mask_arr.shape, 4), dtype=np.uint8)
    overlay_arr[mask_arr > 127] = (*color, int(255 * alpha))
    overlay = Image.fromarray(overlay_arr, mode="RGBA")
    return Image.alpha_composite(img_rgba, overlay).convert("RGB")


def side_by_side(panels, labels, pad=8, label_h=20):
    w, h = panels[0].size
    total_w = w * len(panels) + pad * (len(panels) + 1)
    total_h = h + label_h + pad * 2
    canvas = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    x = pad
    for panel, label in zip(panels, labels):
        canvas.paste(panel, (x, label_h + pad))
        draw.text((x, 2), label, fill=(0, 0, 0))
        x += w + pad
    return canvas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=5,
                         help="number of augmented pairs to save")
    parser.add_argument("--split", type=str, default="train",
                         help="which split to sample from (train shows augmentation)")
    args = parser.parse_args()

    os.makedirs(cfg.OUTPUTS_DIR, exist_ok=True)

    ds = KvasirSegDataset(split=args.split)
    if len(ds) == 0:
        print("Dataset is empty for this split — did you run make_splits.py "
              "and populate data/images, data/masks?")
        return

    n = min(args.n, len(ds))
    norm = cfg.AUGMENTATION_PARAMS["normalize"]

    indices = np.linspace(0, len(ds) - 1, n, dtype=int)
    for k, idx in enumerate(indices):
        image_t, mask_t, stem = ds[idx]
        image_unnorm = unnormalize(image_t, norm["mean"], norm["std"])

        img_pil = tensor_to_pil(image_unnorm)
        mask_pil = mask_tensor_to_pil(mask_t)
        overlay_pil = make_overlay(img_pil, mask_pil)

        canvas = side_by_side(
            [img_pil, mask_pil, overlay_pil],
            ["image (augmented)", "mask (augmented)", "overlay"],
        )
        out_path = os.path.join(cfg.OUTPUTS_DIR, f"sanity_check_{k}_{stem}.png")
        canvas.save(out_path)
        print(f"saved {out_path}")

    print(f"\nDone. Inspect the {n} PNGs in {cfg.OUTPUTS_DIR} — "
          "the red overlay should sit exactly on the polyp region in "
          "every image, confirming mask alignment survived augmentation.")


if __name__ == "__main__":
    main()
