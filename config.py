"""
SDFL — Colorectal Polyp Segmentation
Central config for dataset, splits, hospital simulation, and augmentation.
Owner: Sameer (Step 1b)

Everything downstream (Sanjay's model.py, Mukesh's crypto.py, FL clients)
should import constants from here rather than hardcoding them, so the
whole repo stays in sync with one source of truth.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
MASKS_DIR = os.path.join(DATA_DIR, "masks")
SPLITS_PATH = os.path.join(ROOT_DIR, "splits.json")
HOSPITAL_SPLITS_PATH = os.path.join(ROOT_DIR, "hospital_splits.json")
CHECKPOINT_DIR = os.path.join(ROOT_DIR, "checkpoints")
OUTPUTS_DIR = os.path.join(ROOT_DIR, "outputs")

# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
DATASET_NAME = "Kvasir-SEG"
DATASET_SOURCE_URL = "https://datasets.simula.no/kvasir-seg/"
NUM_IMAGES_EXPECTED = 1000
IMAGE_EXT = ".jpg"
MASK_EXT = ".jpg"

# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------
SEED = 42
TRAIN_FRAC = 0.8
VAL_FRAC = 0.1
TEST_FRAC = 0.1

# Polyp size buckets, by mask foreground area as a fraction of total image area
SIZE_SMALL_MAX = 0.10     # < 10% area  -> "small"
SIZE_MEDIUM_MAX = 0.30    # 10-30% area -> "medium"
                          # > 30% area  -> "large"
SIZE_BUCKETS = ("small", "medium", "large")

# ---------------------------------------------------------------------------
# Non-IID hospital simulation
# ---------------------------------------------------------------------------
NUM_HOSPITALS = 3
HOSPITAL_BIAS_FRAC = 0.8   # 80% of a hospital's pool = its biased class
HOSPITAL_RANDOM_FRAC = 0.2  # 20% random from everything else

# hospital_id -> which size bucket(s) it's biased toward
HOSPITAL_BIAS = {
    0: ("small",),
    1: ("medium",),
    2: ("large", "medium"),  # "large + mixed" per spec
}

# ---------------------------------------------------------------------------
# Augmentation (train split ONLY — never applied to val/test)
# ---------------------------------------------------------------------------
IMG_SIZE = 256

AUGMENTATION_PARAMS = {
    "random_horizontal_flip": {"p": 0.5},
    "random_vertical_flip": {"p": 0.5},
    "random_rotation": {"degrees": 30},
    "color_jitter": {
        "brightness": 0.2,
        "contrast": 0.2,
        "saturation": 0.2,
    },
    "random_resized_crop": {
        "size": IMG_SIZE,
        "scale": (0.8, 1.0),
    },
    "elastic_transform": {
        "alpha": 34.0,
        "sigma": 4.0,
    },
    "normalize": {
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
    },
}

# Order matters: spatial transforms (flip/rotate/crop/elastic) are applied
# identically to image AND mask. Color jitter + normalize are image-only.
AUGMENTATION_ORDER = [
    "random_horizontal_flip",
    "random_vertical_flip",
    "random_rotation",
    "color_jitter",       # image only
    "random_resized_crop",
    "elastic_transform",
    "normalize",           # image only
]

# ---------------------------------------------------------------------------
# Training (E1 baseline — kept here for convenience / Colab single-source)
# ---------------------------------------------------------------------------
E1_CONFIG = {
    "optimizer": "Adam",
    "lr": 1e-4,
    "epochs": 50,
    "batch_size": 8,
    "loss": "DiceBCELoss",
    "target_val_dice": 0.80,
}
