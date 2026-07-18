import os
import sys
import asyncio
import shutil

import pydicom
import numpy as np
import torch
import torchvision.transforms.functional as F
from PIL import Image
from pydicom.pixel_data_handlers.util import apply_voi_lut
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT_DIR, "..", ".."))
sys.path.insert(0, os.path.join(ROOT_DIR, "..", "..", "scripts"))

from model import ResUNetPlusPlus
from e4_dpsgd import fix_model_for_opacus
from e8_server import MCDropoutInference
from scripts.sanitize import sanitize
from platform.client.db import init_db, log_file_status


class DICOMHandler(FileSystemEventHandler):
    def __init__(
        self,
        incoming_dir: str,
        drafts_dir: str,
        rejected_dir: str,
        training_dir: str,
        db_path: str,
    ):
        self.incoming_dir = incoming_dir
        self.drafts_dir = drafts_dir
        self.rejected_dir = rejected_dir
        self.training_dir = training_dir
        self.db_path = db_path

        asyncio.run(init_db(db_path))

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        checkpoint_path = os.path.join(
            ROOT_DIR, "..", "..", "checkpoints", "e8_final.pth"
        )
        self.inference_model = ResUNetPlusPlus()
        state = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
        self.inference_model.load_state_dict(state)
        self.inference_model = fix_model_for_opacus(self.inference_model)
        self.inference_model.to(self.device)
        self.inference_model.eval()

    def on_created(self, event):
        if event.is_directory:
            return
        filepath = event.src_path
        filename = os.path.basename(filepath)
        if not filename.lower().endswith((".dcm", ".dicom")):
            return

        try:
            ds = pydicom.dcmread(filepath)
            pixel_array = ds.pixel_array
            img = apply_voi_lut(pixel_array, ds)
            img = img.astype(np.float32)
            img = (img - img.min()) / (img.max() - img.min() + 1e-8) * 255.0
            img = img.astype(np.uint8)
            if img.ndim == 2:
                img = np.stack([img] * 3, axis=-1)
            elif img.ndim == 3 and img.shape[2] > 3:
                img = img[:, :, :3]
            pil_img = Image.fromarray(img, mode="RGB")

            sanitized_img, passed = sanitize(pil_img)

            if passed:
                img_resized = sanitized_img.resize((256, 256), Image.BILINEAR)
                img_tensor = F.to_tensor(img_resized).unsqueeze(0).to(self.device)
                mc = MCDropoutInference(self.inference_model, n_passes=5)
                result = mc.predict(img_tensor)
                draft_mask = (result["mean_pred"] > 0.5).float()

                sanitized_img.save(os.path.join(self.drafts_dir, f"{filename}.png"))
                mask_np = draft_mask.squeeze().cpu().numpy().astype(np.uint8) * 255
                mask_pil = Image.fromarray(mask_np, mode="L")
                mask_pil.save(os.path.join(self.drafts_dir, f"{filename}_mask.png"))

                inpaint_ratio = 0.0
                asyncio.run(
                    log_file_status(
                        self.db_path, filename, "PASSED", "", inpaint_ratio
                    )
                )
            else:
                dest = os.path.join(self.rejected_dir, filename)
                shutil.move(filepath, dest)
                inpaint_ratio = 0.0
                asyncio.run(
                    log_file_status(
                        self.db_path,
                        filename,
                        "REJECTED",
                        "PHI_GATE_FAILURE",
                        inpaint_ratio,
                    )
                )

        except Exception as e:
            dest = os.path.join(self.rejected_dir, filename)
            shutil.move(filepath, dest)
            asyncio.run(
                log_file_status(
                    self.db_path, filename, "REJECTED", f"ERROR: {e}", 0.0
                )
            )


def promote_to_training(filename: str, drafts_dir: str, training_dir: str):
    images_dir = os.path.join(training_dir, "images")
    masks_dir = os.path.join(training_dir, "masks")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(masks_dir, exist_ok=True)

    src_img = os.path.join(drafts_dir, f"{filename}.png")
    src_mask = os.path.join(drafts_dir, f"{filename}_mask.png")
    if os.path.exists(src_img):
        shutil.move(src_img, os.path.join(images_dir, f"{filename}.png"))
    if os.path.exists(src_mask):
        shutil.move(src_mask, os.path.join(masks_dir, f"{filename}_mask.png"))


def reject_draft(filename: str, drafts_dir: str, rejected_dir: str):
    os.makedirs(rejected_dir, exist_ok=True)
    for ext in (".png", "_mask.png"):
        src = os.path.join(drafts_dir, f"{filename}{ext}")
        if os.path.exists(src):
            shutil.move(src, os.path.join(rejected_dir, f"{filename}{ext}"))


def start_watcher(config) -> Observer:
    incoming = config["incoming_dir"]
    drafts = config["drafts_dir"]
    rejected = config["rejected_dir"]
    training = config["training_dir"]
    db_path = config["db_path"]

    os.makedirs(incoming, exist_ok=True)
    os.makedirs(drafts, exist_ok=True)
    os.makedirs(rejected, exist_ok=True)
    os.makedirs(training, exist_ok=True)

    handler = DICOMHandler(incoming, drafts, rejected, training, db_path)
    observer = Observer()
    observer.schedule(handler, incoming, recursive=False)
    observer.start()
    return observer
