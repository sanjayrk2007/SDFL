"""
SDFL — PyTorch Dataset for Kvasir-SEG
Owner: Sameer (Step 1b)

KvasirSegDataset reads splits.json (and optionally hospital_splits.json)
to serve the right filenames for:
    - a given split: "train" / "val" / "test"
    - a given hospital client: hospital_id in {0, 1, 2}, intersected with
      a split (so each FL client still has its own train/val/test if needed)

Augmentation is applied only when split == "train", per the project spec.
Sanjay's E6 sanitize() hook point is marked below for when that pipeline
lands — it slots in BEFORE augmentation, exactly as his spec requires.
"""

import os
import sys
import json

from PIL import Image
from torch.utils.data import Dataset

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg
from joint_transforms import JointTransform


class KvasirSegDataset(Dataset):
    def __init__(self, split="train", hospital_id=None,
                 splits_path=cfg.SPLITS_PATH,
                 hospital_splits_path=cfg.HOSPITAL_SPLITS_PATH,
                 images_dir=cfg.IMAGES_DIR, masks_dir=cfg.MASKS_DIR,
                 sanitize_fn=None):
        """
        split:        "train" | "val" | "test"
        hospital_id:  None for centralized (E1), or 0/1/2 for FL clients (E2+).
                      When set, filenames are restricted to that hospital's
                      assignment AND the requested split.
        sanitize_fn:  optional callable(PIL.Image) -> (PIL.Image, bool).
                      Hook for Sanjay's E6 sanitize.py. Applied before
                      augmentation. If it returns flag=False, the sample
                      is treated as filtered (skipped) at __getitem__ time
                      is not possible in standard PyTorch Datasets, so
                      filtering happens once in __init__ via
                      self._filter_unsanitized().
        """
        assert split in ("train", "val", "test")
        self.split = split
        self.hospital_id = hospital_id
        self.images_dir = images_dir
        self.masks_dir = masks_dir
        self.sanitize_fn = sanitize_fn

        with open(splits_path, "r") as f:
            splits_data = json.load(f)
        split_stems = set(splits_data["splits"][split])

        if hospital_id is not None:
            with open(hospital_splits_path, "r") as f:
                hosp_data = json.load(f)
            hospital_stems = set(hosp_data["hospitals"][str(hospital_id)]["filenames"])
            stems = sorted(split_stems & hospital_stems)
        else:
            stems = sorted(split_stems)

        self.stems = stems
        self.transform = JointTransform(train=(split == "train"))

        if self.sanitize_fn is not None:
            self._filter_unsanitized()

    def _filter_unsanitized(self):
        """Run sanitize_fn once over all stems and drop any flagged False.
        Logs skipped filenames to skipped_samples.log per Sanjay's E6 spec."""
        kept = []
        skipped_log_path = os.path.join(cfg.ROOT_DIR, "skipped_samples.log")
        with open(skipped_log_path, "a") as logf:
            for stem in self.stems:
                img_path = os.path.join(self.images_dir, stem + cfg.IMAGE_EXT)
                img = Image.open(img_path).convert("RGB")
                _, flag = self.sanitize_fn(img)
                if flag:
                    kept.append(stem)
                else:
                    logf.write(stem + "\n")
        self.stems = kept

    def __len__(self):
        return len(self.stems)

    def __getitem__(self, idx):
        stem = self.stems[idx]
        img_path = os.path.join(self.images_dir, stem + cfg.IMAGE_EXT)
        mask_path = os.path.join(self.masks_dir, stem + cfg.MASK_EXT)

        image = Image.open(img_path).convert("RGB")
        mask = Image.open(mask_path).convert("L")

        # Sanitization hook (E6): runs before augmentation, image only.
        # Filtering already happened in __init__; here we just apply the
        # cleanup transform (CLAHE/inpaint/EXIF scrub) to the kept samples.
        if self.sanitize_fn is not None:
            image, _ = self.sanitize_fn(image)

        image, mask = self.transform(image, mask)
        return image, mask, stem


def get_dataloaders(batch_size=8, hospital_id=None, num_workers=2,
                     sanitize_fn=None):
    """Convenience builder used by E1 (hospital_id=None) and E2+ FL clients
    (hospital_id=0/1/2)."""
    from torch.utils.data import DataLoader

    train_ds = KvasirSegDataset(split="train", hospital_id=hospital_id,
                                 sanitize_fn=sanitize_fn)
    val_ds = KvasirSegDataset(split="val", hospital_id=hospital_id,
                               sanitize_fn=sanitize_fn)
    test_ds = KvasirSegDataset(split="test", hospital_id=hospital_id,
                                sanitize_fn=sanitize_fn)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                               num_workers=num_workers, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                             num_workers=num_workers)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False,
                              num_workers=num_workers)

    return train_loader, val_loader, test_loader
