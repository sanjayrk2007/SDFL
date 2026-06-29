import os
import sys
import json
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as T
import PIL.Image
from torch.utils.data import DataLoader
import flwr as fl

# Ensure workspace root and scripts folder are in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

import config as cfg
from joint_transforms import JointTransform
from sanitize import sanitize
from model import ResUNetPlusPlus
from losses import DiceBCELoss
from e2_server import DEVICE
from crypto import client_encrypt

try:
    from e5_server import SecAggDPSGDHospitalClient, CheckpointingSecAgg, weighted_average
except ImportError:
    from e5_secagg import SecAggDPSGDHospitalClient, CheckpointingSecAgg, weighted_average

from e4_dpsgd import fix_model_for_opacus, get_parameters, set_parameters

class SkipSample(Exception):
    pass

class SanitizedKvasirDataset(torch.utils.data.Dataset):
    def __init__(self, image_paths, mask_paths, augment=False, log_file="skipped_samples.log"):
        self.image_paths = image_paths
        self.mask_paths = mask_paths
        self.augment = augment
        self.log_file = log_file
        
        self.joint_transform_train = JointTransform(train=True)
        self.resize_img = T.Resize((256, 256), interpolation=T.InterpolationMode.BILINEAR)
        self.resize_mask = T.Resize((256, 256), interpolation=T.InterpolationMode.NEAREST)
        self.to_tensor = T.ToTensor()
        self.normalize = T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        try:
            image = PIL.Image.open(self.image_paths[idx]).convert("RGB")
            mask = PIL.Image.open(self.mask_paths[idx]).convert("L")
            
            clean_image, passed = sanitize(image)
            if not passed:
                log_entry = {
                    "filename": self.image_paths[idx],
                    "reason": "PHI_gate",
                    "timestamp": time.time()
                }
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
                raise SkipSample()
                
            if self.augment:
                image_tensor, mask_tensor = self.joint_transform_train(clean_image, mask)
            else:
                clean_image = self.resize_img(clean_image)
                mask = self.resize_mask(mask)
                image_tensor = self.to_tensor(clean_image)
                image_tensor = self.normalize(image_tensor)
                mask_tensor = self.to_tensor(mask)
                
            return (image_tensor, mask_tensor)
        except SkipSample as e:
            return e

def sanitized_collate_fn(batch):
    valid_samples = [s for s in batch if not isinstance(s, SkipSample)]
    if len(valid_samples) == 0:
        return None
    from torch.utils.data.dataloader import default_collate
    return default_collate(valid_samples)

def dice_iou_score(pred, target, eps=1e-7):
    pred_bin = (pred > 0.5).float()
    intersection = (pred_bin * target).sum(dim=(1, 2, 3))
    union = pred_bin.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3))
    dice = (2 * intersection + eps) / (union + eps)
    iou = (intersection + eps) / (union - intersection + eps)
    return dice.mean().item(), iou.mean().item()

class SanitizedSecAggDPSGDHospitalClient(SecAggDPSGDHospitalClient):
    def __init__(self, hospital_id, local_epochs=3, mu=0.0, max_grad_norm=1.0, noise_multiplier=1.0):
        # Retrieve partitioning details and configure client datasets
        with open(cfg.SPLITS_PATH, "r") as f:
            splits_data = json.load(f)
        with open(cfg.HOSPITAL_SPLITS_PATH, "r") as f:
            hosp_data = json.load(f)
            
        hospital_stems = set(hosp_data["hospitals"][str(hospital_id)]["filenames"])
        
        # Train paths
        train_stems = sorted(set(splits_data["splits"]["train"]) & hospital_stems)
        train_image_paths = [os.path.join(cfg.IMAGES_DIR, stem + cfg.IMAGE_EXT) for stem in train_stems]
        train_mask_paths = [os.path.join(cfg.MASKS_DIR, stem + cfg.MASK_EXT) for stem in train_stems]
        
        # Val paths
        val_stems = sorted(set(splits_data["splits"]["val"]) & hospital_stems)
        val_image_paths = [os.path.join(cfg.IMAGES_DIR, stem + cfg.IMAGE_EXT) for stem in val_stems]
        val_mask_paths = [os.path.join(cfg.MASKS_DIR, stem + cfg.MASK_EXT) for stem in val_stems]
        
        # Setup Sanitized Data Loaders
        train_ds = SanitizedKvasirDataset(train_image_paths, train_mask_paths, augment=True)
        val_ds = SanitizedKvasirDataset(val_image_paths, val_mask_paths, augment=False)
        
        trainloader = DataLoader(train_ds, batch_size=8, shuffle=True, collate_fn=sanitized_collate_fn)
        valloader = DataLoader(val_ds, batch_size=8, shuffle=False, collate_fn=sanitized_collate_fn)
        
        super().__init__(
            hospital_id=hospital_id,
            trainloader=trainloader,
            valloader=valloader,
            local_epochs=local_epochs,
            mu=mu,
            max_grad_norm=max_grad_norm,
            noise_multiplier=noise_multiplier
        )

    def fit(self, parameters, config):
        key_hex = config["round_key_hex"]
        round_key = bytes.fromhex(key_hex)

        underlying_model = self.model._module if hasattr(self.model, "_module") else self.model
        set_parameters(underlying_model, parameters)
        
        global_model = ResUNetPlusPlus().to(DEVICE)
        fix_model_for_opacus(global_model)
        global_model.to(DEVICE)
        set_parameters(global_model, parameters)
        for p in global_model.parameters():
            p.requires_grad = False
            
        self.model.train()
        global_model.eval()
        total_loss, n_batches = 0.0, 0
        for _ in range(self.local_epochs):
            for batch in self.trainloader:
                if batch is None:
                    continue
                images, masks = batch
                images, masks = images.to(DEVICE), masks.to(DEVICE)
                self.optimizer.zero_grad()
                preds = self.model(images)
                base_loss = self.loss_fn(preds, masks)
                prox_loss = 0.0
                if self.mu > 0.0:
                    for lp, gp in zip(underlying_model.parameters(), global_model.parameters()):
                        prox_loss += torch.sum((lp - gp) ** 2)
                loss = base_loss + (self.mu / 2.0) * prox_loss
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()
                n_batches += 1
                
        avg_loss = total_loss / max(n_batches, 1)
        epsilon = self.privacy_engine.get_epsilon(delta=1e-5)
        del global_model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        weights = get_parameters(underlying_model)
        ct = client_encrypt(weights, round_key)
        del weights
        
        metrics = {
            "hospital_id": self.hospital_id,
            "train_loss": avg_loss,
            "epsilon": epsilon,
            "nonce_hex": ct["nonce"].hex(),
            "ciphertext_hex": ct["ciphertext"].hex()
        }
        
        dummy_weights = [np.zeros(1) for _ in range(len(parameters))]
        return dummy_weights, len(self.trainloader.dataset), metrics

    def evaluate(self, parameters, config):
        underlying_model = self.model._module if hasattr(self.model, "_module") else self.model
        set_parameters(underlying_model, parameters)
        self.model.eval()
        total_loss, total_dice, total_iou, n_batches = 0.0, 0.0, 0.0, 0
        with torch.no_grad():
            for batch in self.valloader:
                if batch is None:
                    continue
                images, masks = batch
                images, masks = images.to(DEVICE), masks.to(DEVICE)
                preds = self.model(images)
                loss = self.loss_fn(preds, masks)
                dice, iou = dice_iou_score(preds, masks)
                total_loss += loss.item()
                total_dice += dice
                total_iou += iou
                n_batches += 1
                
        avg_loss = total_loss / max(n_batches, 1)
        avg_dice = total_dice / max(n_batches, 1)
        avg_iou = total_iou / max(n_batches, 1)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return (avg_loss, len(self.valloader.dataset),
                {"hospital_id": self.hospital_id, "val_dice": avg_dice, "val_iou": avg_iou})

class E6CheckpointingSecAgg(CheckpointingSecAgg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.round_history = []

    def aggregate_evaluate(self, server_round, results, failures):
        agg_loss, avg_metrics = super().aggregate_evaluate(server_round, results, failures)
        if avg_metrics is not None:
            val_dice = avg_metrics.get("val_dice", 0.0)
            val_iou = avg_metrics.get("val_iou", 0.0)
            self.round_history.append((server_round, val_dice, val_iou))
            print(f"Round {server_round:2d}/20 | val_loss {agg_loss:.4f} | "
                  f"val_dice {val_dice:.4f} | val_iou {val_iou:.4f}")
        return agg_loss, avg_metrics

def get_client_fn(mu, max_grad_norm, noise_multiplier):
    def client_fn(context: fl.common.Context):
        hid = int(context.node_config["partition-id"])
        client = SanitizedSecAggDPSGDHospitalClient(
            hospital_id=hid,
            local_epochs=3,
            mu=mu,
            max_grad_norm=max_grad_norm,
            noise_multiplier=noise_multiplier
        )
        return client.to_client()
    return client_fn

def run_e6_simulation():
    # 1. Reset/delete skipped_samples.log if it exists
    log_path = "skipped_samples.log"
    if os.path.exists(log_path):
        os.remove(log_path)

    # 2. Load initial weights from checkpoints/e5_best.pth
    initial_model = ResUNetPlusPlus().to(DEVICE)
    fix_model_for_opacus(initial_model)
    initial_model.to(DEVICE)
    checkpoint_path = "checkpoints/e5_best.pth"
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    initial_model.load_state_dict(torch.load(checkpoint_path, map_location=DEVICE))
    initial_parameters = fl.common.ndarrays_to_parameters(get_parameters(initial_model))

    # Config parameters
    mu = 0.001
    C = 2.0
    sigma = 1.5
    num_rounds = 20

    strategy = E6CheckpointingSecAgg(
        mu=mu,
        C=C,
        sigma=sigma,
        initial_parameters=initial_parameters,
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=3,
        min_evaluate_clients=3,
        min_available_clients=3,
    )

    python_path = os.pathsep.join([ROOT_DIR, os.path.join(ROOT_DIR, "scripts")])
    client_resources = {"num_cpus": 1, "num_gpus": 0.33}

    print("Starting E6 Federated Learning simulation...")
    fl.simulation.start_simulation(
        client_fn=get_client_fn(mu, C, sigma),
        num_clients=3,
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
        client_resources=client_resources,
        ray_init_args={
            "runtime_env": {
                "env_vars": {"PYTHONPATH": python_path}
            }
        }
    )

    # Save model to checkpoints/e6_best.pth
    if strategy.latest_ndarrays is not None:
        best_model = ResUNetPlusPlus().to(DEVICE)
        fix_model_for_opacus(best_model)
        set_parameters(best_model, strategy.latest_ndarrays)
        os.makedirs("checkpoints", exist_ok=True)
        torch.save(best_model.state_dict(), "checkpoints/e6_best.pth")
        print("Saved best model to checkpoints/e6_best.pth")

    # Print val_dice per round
    print("\n--- Val Dice Per Round ---")
    for rnd, dice, iou in strategy.round_history:
        print(f"Round {rnd:2d} | val_dice: {dice:.4f} | val_iou: {iou:.4f}")

    # Print final val_dice, val_iou, epsilon
    final_dice = strategy.latest_metrics.get("val_dice", 0.0)
    final_iou = strategy.latest_metrics.get("val_iou", 0.0)
    epsilon = strategy.latest_metrics.get("epsilon", 0.0)
    print("\n--- Final Metrics ---")
    print(f"Final val_dice: {final_dice:.4f}")
    print(f"Final val_iou: {final_iou:.4f}")
    print(f"Final epsilon: {epsilon:.4f}")

    # Print total skipped samples
    skipped_count = 0
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            skipped_count = len(f.readlines())
    print(f"Total skipped samples: {skipped_count}")

if __name__ == "__main__":
    run_e6_simulation()
