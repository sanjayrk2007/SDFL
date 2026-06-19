"""
SDFL — Split generator
Owner: Sameer (Step 1b)

Produces:
    splits.json          -> stratified train/val/test indices (by polyp size)
    hospital_splits.json -> non-IID 3-hospital simulation

Run:
    python scripts/make_splits.py

Polyp size is computed from each mask's foreground pixel fraction:
    small  : area < 10%
    medium : 10% <= area < 30%
    large  : area >= 30%

Stratification keeps the train/val/test ratio consistent across all three
size buckets. Hospital assignment is then layered on top of the same
filename list (hospitals draw from the full dataset, not just train).
"""

import os
import sys
import json
import random

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg


def compute_polyp_area_fraction(mask_path: str) -> float:
    """Fraction of pixels that are foreground (polyp) in a binary mask."""
    mask = Image.open(mask_path).convert("L")
    arr = np.array(mask)
    # Kvasir-SEG masks are near-binary jpgs; threshold at mid-gray to be safe
    binary = (arr > 127).astype(np.uint8)
    return float(binary.sum()) / float(binary.size)


def bucket_for_area(area_frac: float) -> str:
    if area_frac < cfg.SIZE_SMALL_MAX:
        return "small"
    elif area_frac < cfg.SIZE_MEDIUM_MAX:
        return "medium"
    else:
        return "large"


def list_dataset_filenames():
    """Return sorted list of image filenames (without ext) present in both
    images/ and masks/ dirs. Sorting first keeps the split deterministic
    before we even touch the RNG."""
    if not os.path.isdir(cfg.IMAGES_DIR):
        raise FileNotFoundError(
            f"Images dir not found: {cfg.IMAGES_DIR}\n"
            f"Download Kvasir-SEG from {cfg.DATASET_SOURCE_URL} and place "
            f"images/masks under data/ before running this script."
        )
    img_files = sorted(
        f for f in os.listdir(cfg.IMAGES_DIR) if f.lower().endswith(cfg.IMAGE_EXT)
    )
    stems = [os.path.splitext(f)[0] for f in img_files]
    return stems


def stratified_split(stems_by_bucket: dict, seed: int):
    """80/10/10 split applied independently within each size bucket,
    then merged. Returns dict[split_name] -> list[filename_stem]."""
    rng = random.Random(seed)
    splits = {"train": [], "val": [], "test": []}

    for bucket_name, stems in stems_by_bucket.items():
        stems = list(stems)
        rng.shuffle(stems)
        n = len(stems)
        n_train = int(round(n * cfg.TRAIN_FRAC))
        n_val = int(round(n * cfg.VAL_FRAC))
        # remainder goes to test so rounding never drops a sample
        train_stems = stems[:n_train]
        val_stems = stems[n_train:n_train + n_val]
        test_stems = stems[n_train + n_val:]

        splits["train"].extend(train_stems)
        splits["val"].extend(val_stems)
        splits["test"].extend(test_stems)

    return splits


def assign_hospitals(stems_by_bucket: dict, seed: int):
    """Non-IID 3-hospital simulation.

    Each hospital draws:
        80% from its biased bucket(s) (cfg.HOSPITAL_BIAS)
        20% randomly from the remaining pool (any bucket)

    Sampling is WITH replacement disabled — once a stem is drawn for a
    hospital's biased pool it's removed from that pool so hospitals don't
    trivially overlap on the biased portion. The random 20% is drawn from
    the full dataset and MAY overlap across hospitals (real hospitals would
    share some general-population cases too).
    """
    rng = random.Random(seed + 1)  # offset so hospital RNG != split RNG

    all_stems = [s for bucket in stems_by_bucket.values() for s in bucket]
    total_n = len(all_stems)

    # Target hospital size: split the dataset evenly across hospitals
    per_hospital_n = total_n // cfg.NUM_HOSPITALS

    # mutable copies we can pop from for the "biased" draw
    pools = {b: list(stems) for b, stems in stems_by_bucket.items()}
    for p in pools.values():
        rng.shuffle(p)

    hospital_assignments = {}

    for hid in range(cfg.NUM_HOSPITALS):
        biased_buckets = cfg.HOSPITAL_BIAS[hid]
        n_biased = int(round(per_hospital_n * cfg.HOSPITAL_BIAS_FRAC))
        n_random = per_hospital_n - n_biased

        # pull biased portion round-robin across this hospital's bucket(s)
        biased_draw = []
        bucket_cycle = list(biased_buckets)
        i = 0
        while len(biased_draw) < n_biased:
            b = bucket_cycle[i % len(bucket_cycle)]
            if pools[b]:
                biased_draw.append(pools[b].pop())
            elif not any(pools[bb] for bb in bucket_cycle):
                break  # all biased pools exhausted, stop early
            i += 1

        # pull random portion from the full dataset (allowed to overlap
        # with other hospitals' random portions, but not with this
        # hospital's own biased_draw)
        remaining_pool = [s for s in all_stems if s not in biased_draw]
        rng.shuffle(remaining_pool)
        random_draw = remaining_pool[:n_random]

        hospital_assignments[hid] = {
            "biased_buckets": list(biased_buckets),
            "filenames": sorted(set(biased_draw + random_draw)),
            "n_biased": len(biased_draw),
            "n_random": len(random_draw),
        }

    return hospital_assignments


def main():
    print(f"[1/4] Listing dataset files in {cfg.IMAGES_DIR} ...")
    stems = list_dataset_filenames()
    print(f"      Found {len(stems)} image files.")
    if len(stems) != cfg.NUM_IMAGES_EXPECTED:
        print(f"      WARNING: expected {cfg.NUM_IMAGES_EXPECTED}, "
              f"found {len(stems)}. Continuing anyway.")

    print("[2/4] Computing polyp size bucket for each mask ...")
    stems_by_bucket = {b: [] for b in cfg.SIZE_BUCKETS}
    bucket_of = {}
    for stem in stems:
        mask_path = os.path.join(cfg.MASKS_DIR, stem + cfg.MASK_EXT)
        if not os.path.exists(mask_path):
            print(f"      WARNING: missing mask for {stem}, skipping.")
            continue
        area = compute_polyp_area_fraction(mask_path)
        b = bucket_for_area(area)
        stems_by_bucket[b].append(stem)
        bucket_of[stem] = {"bucket": b, "area_frac": round(area, 6)}

    for b, s in stems_by_bucket.items():
        print(f"      {b:>6}: {len(s)} images")

    print(f"[3/4] Stratified {int(cfg.TRAIN_FRAC*100)}/"
          f"{int(cfg.VAL_FRAC*100)}/{int(cfg.TEST_FRAC*100)} split "
          f"(seed={cfg.SEED}) ...")
    splits = stratified_split(stems_by_bucket, seed=cfg.SEED)
    for split_name, split_stems in splits.items():
        print(f"      {split_name:>5}: {len(split_stems)} images")

    splits_out = {
        "seed": cfg.SEED,
        "train_frac": cfg.TRAIN_FRAC,
        "val_frac": cfg.VAL_FRAC,
        "test_frac": cfg.TEST_FRAC,
        "size_buckets": {
            "small_max": cfg.SIZE_SMALL_MAX,
            "medium_max": cfg.SIZE_MEDIUM_MAX,
        },
        "bucket_of": bucket_of,
        "splits": splits,
    }
    with open(cfg.SPLITS_PATH, "w") as f:
        json.dump(splits_out, f, indent=2)
    print(f"      Saved -> {cfg.SPLITS_PATH}")

    print(f"[4/4] Building non-IID hospital splits (seed={cfg.SEED}) ...")
    hospital_assignments = assign_hospitals(stems_by_bucket, seed=cfg.SEED)
    for hid, info in hospital_assignments.items():
        print(f"      Hospital {hid} (bias={info['biased_buckets']}): "
              f"{len(info['filenames'])} images "
              f"({info['n_biased']} biased + {info['n_random']} random)")

    hospital_out = {
        "seed": cfg.SEED,
        "num_hospitals": cfg.NUM_HOSPITALS,
        "bias_frac": cfg.HOSPITAL_BIAS_FRAC,
        "random_frac": cfg.HOSPITAL_RANDOM_FRAC,
        "hospitals": {
            str(hid): info for hid, info in hospital_assignments.items()
        },
    }
    with open(cfg.HOSPITAL_SPLITS_PATH, "w") as f:
        json.dump(hospital_out, f, indent=2)
    print(f"      Saved -> {cfg.HOSPITAL_SPLITS_PATH}")

    print("\nDone. splits.json + hospital_splits.json are ready.")


if __name__ == "__main__":
    main()
