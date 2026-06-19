"""
SDFL — Colab/local dataset setup helper
Owner: Sameer (Step 1b)

Downloads Kvasir-SEG and arranges it into:
    data/images/*.jpg
    data/masks/*.jpg

Kvasir-SEG ships as a single zip containing Kvasir-SEG/images/ and
Kvasir-SEG/masks/ subfolders — this script unzips it directly into
data/, matching the layout config.py expects.

Run (Colab cell or terminal):
    python scripts/setup_data.py

If you already have the dataset downloaded locally, just copy/symlink:
    data/images/  <- your *.jpg images
    data/masks/   <- your *.jpg masks (same filenames as images)
and skip this script.
"""

import os
import sys
import shutil
import zipfile
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as cfg

KVASIR_ZIP_URL = "https://datasets.simula.no/downloads/kvasir-seg.zip"


def download_with_progress(url, dest_path):
    def report(block_num, block_size, total_size):
        downloaded = block_num * block_size
        pct = min(100, downloaded * 100 / total_size) if total_size > 0 else 0
        print(f"\r  downloading: {pct:5.1f}%", end="", flush=True)

    urllib.request.urlretrieve(url, dest_path, reporthook=report)
    print()


def main():
    if os.path.isdir(cfg.IMAGES_DIR) and os.listdir(cfg.IMAGES_DIR):
        print(f"data/images already populated ({len(os.listdir(cfg.IMAGES_DIR))} "
              f"files found) — skipping download. Delete the folder contents "
              f"to force a re-download.")
        return

    tmp_zip = os.path.join(cfg.ROOT_DIR, "_kvasir_seg_tmp.zip")
    tmp_extract = os.path.join(cfg.ROOT_DIR, "_kvasir_seg_extract")

    print(f"Downloading Kvasir-SEG from {KVASIR_ZIP_URL} ...")
    try:
        download_with_progress(KVASIR_ZIP_URL, tmp_zip)
    except Exception as e:
        print(f"\nDownload failed: {e}")
        print(f"Please manually download from {cfg.DATASET_SOURCE_URL} "
              f"and place images/masks under {cfg.DATA_DIR}")
        return

    print("Extracting ...")
    os.makedirs(tmp_extract, exist_ok=True)
    with zipfile.ZipFile(tmp_zip, "r") as zf:
        zf.extractall(tmp_extract)

    # locate the images/ and masks/ subfolders wherever they landed
    images_src, masks_src = None, None
    for root, dirs, files in os.walk(tmp_extract):
        if os.path.basename(root).lower() == "images":
            images_src = root
        elif os.path.basename(root).lower() == "masks":
            masks_src = root

    if images_src is None or masks_src is None:
        print("Could not locate images/masks folders inside the downloaded "
              "zip. Please inspect _kvasir_seg_extract/ manually and copy "
              "the contents into data/images and data/masks.")
        return

    os.makedirs(cfg.IMAGES_DIR, exist_ok=True)
    os.makedirs(cfg.MASKS_DIR, exist_ok=True)

    for fname in os.listdir(images_src):
        shutil.copy(os.path.join(images_src, fname), os.path.join(cfg.IMAGES_DIR, fname))
    for fname in os.listdir(masks_src):
        shutil.copy(os.path.join(masks_src, fname), os.path.join(cfg.MASKS_DIR, fname))

    print(f"Copied {len(os.listdir(cfg.IMAGES_DIR))} images and "
          f"{len(os.listdir(cfg.MASKS_DIR))} masks into {cfg.DATA_DIR}")

    os.remove(tmp_zip)
    shutil.rmtree(tmp_extract)
    print("Cleanup done. Next step: python scripts/make_splits.py")


if __name__ == "__main__":
    main()
