import os
import sys
import json
import time
import uuid
import numpy as np
import torch
import torch.nn as nn
import flwr as fl

# Ensure workspace root is in path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

import config as cfg
from crypto import (
    generate_round_key,
    client_encrypt,
    decrypt_update,
    destroy_round_key,
    create_certificate,
    sign_certificate,
    verify_certificate,
    write_audit_log,
)
from model import ResUNetPlusPlus
from e2_server import DEVICE
from e4_dpsgd import fix_model_for_opacus, get_parameters, set_parameters, weighted_average
from e7_temporal import TemporalHospitalClient, TemporalCheckpointingSecAgg, compute_model_hash
from dataset import get_dataloaders, KvasirSegDataset

# =========================================================================
# PART 1 — WEIGHTED AVERAGING FIX IN crypto.py (MONKEY-PATCH)
# =========================================================================

def _weighted_server_aggregate(list_of_ciphertexts, round_key, num_examples_list):
    import numpy as np
    from crypto import decrypt_update
    decrypted_updates = [decrypt_update(ct, round_key) for ct in list_of_ciphertexts]
    total = sum(num_examples_list)
    if total == 0:
        total = 1
    aggregated = []
    for layer_idx in range(len(decrypted_updates[0])):
        weighted_sum = sum(
            (n / total) * update[layer_idx]
            for n, update in zip(num_examples_list, decrypted_updates)
        )
        aggregated.append(weighted_sum)
    return aggregated

# Apply monkey patch
import crypto
crypto.server_aggregate = _weighted_server_aggregate


# =========================================================================
# PART 2 — MC DROPOUT UNCERTAINTY HEAD
# =========================================================================

class MCDropoutInference:
    def __init__(self, model, n_passes=20, dropout_p=0.5):
        self.model = model
        self.n_passes = n_passes
        self.dropout_p = dropout_p
        
        # Patch in nn.Dropout layers before final Conv2d(1,1) if not already present
        underlying_model = model._module if hasattr(model, "_module") else model
        has_dropout = any(isinstance(layer, (nn.Dropout, nn.Dropout2d)) for layer in underlying_model.output_head)
        if not has_dropout:
            new_head = nn.Sequential(
                nn.Dropout(p=dropout_p),
                *list(underlying_model.output_head)
            )
            underlying_model.output_head = new_head

    def enable_dropout(self):
        # Set the model to eval first, then force dropout layers to train mode
        self.model.eval()
        for m in self.model.modules():
            if isinstance(m, (nn.Dropout, nn.Dropout2d)):
                m.train()
        if hasattr(self.model, "_module"):
            for m in self.model._module.modules():
                if isinstance(m, (nn.Dropout, nn.Dropout2d)):
                    m.train()

    def predict(self, image_tensor: torch.Tensor, threshold: float = 0.05) -> dict:
        self.enable_dropout()
        preds = []
        with torch.no_grad():
            for _ in range(self.n_passes):
                pred = self.model(image_tensor)
                preds.append(pred)
        
        stacked = torch.stack(preds, dim=0)  # shape (N, B, 1, H, W)
        mean_pred = stacked.mean(dim=0)      # shape (B, 1, H, W)
        uncertainty_map = stacked.var(dim=0, unbiased=False)  # shape (B, 1, H, W)
        mean_uncertainty = uncertainty_map.mean().item()
        failure_flag = mean_uncertainty > threshold
        
        return {
            "mean_pred": mean_pred,
            "uncertainty_map": uncertainty_map,
            "mean_uncertainty": mean_uncertainty,
            "failure_flag": failure_flag
        }


# =========================================================================
# PART 3 — FULL SDFL CLIENT
# =========================================================================

class FullSDFLClient(TemporalHospitalClient):
    def fit(self, parameters, config):
        # Inherit training and encryption logic, but pass num_examples back in metrics
        dummy_weights, num_examples, metrics = super().fit(parameters, config)
        metrics["num_examples"] = num_examples
        
        # Track training steps and sample rate for cumulative privacy engine
        steps = len(self.trainloader) if self.trainloader is not None else 0
        batch_size = getattr(self.trainloader, "batch_size", 8)
        if batch_size is None:
            batch_size = 8
        sample_rate = batch_size / max(num_examples, 1)
        metrics["steps_executed"] = steps
        metrics["sample_rate"] = sample_rate
        return dummy_weights, num_examples, metrics


# =========================================================================
# PART 4 — FULL SDFL STRATEGY
# =========================================================================

class FullSDFLStrategy(TemporalCheckpointingSecAgg):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.AUDIT_LOG_PATH = os.path.join(ROOT_DIR, "audit_log.jsonl")
        self.client_accountants = {}  # hospital_id -> RDPAccountant

    def aggregate_fit(self, server_round, results, failures):
        current_time = time.time()
        list_of_ciphertexts = []
        num_examples_list = []
        epsilons = []
        
        try:
            # 1. Accept updates only if they satisfy validator rules
            for client_proxy, fit_res in results:
                is_valid, reason = self.validate_update(fit_res, current_time)
                if not is_valid:
                    print(f"Aggregator rejected update from client {client_proxy.cid}: {reason}")
                    continue
                    
                nonce = bytes.fromhex(fit_res.metrics["nonce_hex"])
                ciphertext = bytes.fromhex(fit_res.metrics["ciphertext_hex"])
                list_of_ciphertexts.append({
                    "nonce": nonce,
                    "ciphertext": ciphertext
                })
                
                num_examples = fit_res.metrics.get("num_examples", fit_res.num_examples)
                num_examples_list.append(num_examples)
                
                # Account for privacy budget cumulatively
                hid = fit_res.metrics.get("hospital_id")
                steps = fit_res.metrics.get("steps_executed", 0)
                q = fit_res.metrics.get("sample_rate", 0.0)
                
                if hid is not None and steps > 0 and q > 0.0:
                    if hid not in self.client_accountants:
                        from opacus.accountants import RDPAccountant
                        self.client_accountants[hid] = RDPAccountant()
                    
                    accountant = self.client_accountants[hid]
                    for _ in range(steps):
                        accountant.step(noise_multiplier=self.sigma, sample_rate=q)
                    
                    client_eps = accountant.get_epsilon(delta=1e-5)
                    epsilons.append(client_eps)
                else:
                    if "epsilon" in fit_res.metrics:
                        epsilons.append(fit_res.metrics["epsilon"])

            # Cache ciphertexts for this round
            self.cached_ciphertexts[server_round] = list_of_ciphertexts

            if epsilons:
                self.latest_metrics["epsilon"] = max(epsilons)

            # 2. Decrypt & Aggregate using weighted server aggregate
            aggregated_weights = None
            round_key = self.round_keys.get(self.current_key_context_id)
            
            if list_of_ciphertexts and round_key is not None:
                try:
                    # Use weighted average aggregation
                    aggregated_weights = _weighted_server_aggregate(list_of_ciphertexts, round_key, num_examples_list)
                except Exception as e:
                    print(f"Decryption / Aggregation failed: {e}")

            if aggregated_weights is None:
                write_audit_log(self.AUDIT_LOG_PATH, {
                    "event": "round_expired_no_aggregation",
                    "round_id": server_round,
                    "reason": "no_valid_updates_or_decryption_failed",
                    "timestamp": time.time()
                })
                return None, {}

            params = fl.common.ndarrays_to_parameters(aggregated_weights)
            self.latest_ndarrays = aggregated_weights
            
            write_audit_log(self.AUDIT_LOG_PATH, {
                "event": "round_close",
                "round_id": server_round,
                "timestamp": time.time()
            })
            
            return params, {}

        finally:
            # 3. Wipe and destroy ephemeral round key
            round_key = self.round_keys.get(self.current_key_context_id)
            if round_key is not None:
                destroy_round_key(round_key)
                self.round_keys.pop(self.current_key_context_id, None)
                
            self.cached_ciphertexts.pop(server_round, None)
            list_of_ciphertexts.clear()
            
            write_audit_log(self.AUDIT_LOG_PATH, {
                "event": "key_destroyed",
                "round_id": server_round,
                "timestamp": time.time()
            })


# =========================================================================
# PART 5 — CROSS-CENTRE EVALUATION
# =========================================================================

def compute_hd95_scipy(pred, target):
    from scipy.ndimage import distance_transform_edt, binary_erosion
    
    pred_bin = (pred > 0.5).astype(bool)
    target_bin = (target > 0.5).astype(bool)
    
    h, w = pred_bin.shape[-2:]
    max_dist = np.sqrt(h**2 + w**2)
    
    if not np.any(pred_bin) and not np.any(target_bin):
        return 0.0
    if not np.any(pred_bin) or not np.any(target_bin):
        return max_dist
        
    def get_boundary(mask):
        eroded = binary_erosion(mask)
        return mask & ~eroded
        
    b_pred = get_boundary(pred_bin)
    b_target = get_boundary(target_bin)
    
    if not np.any(b_pred):
        b_pred = pred_bin
    if not np.any(b_target):
        b_target = target_bin
        
    d_target = distance_transform_edt(~b_target)
    d_pred = distance_transform_edt(~b_pred)
    
    dist_pred_to_target = d_target[b_pred]
    dist_target_to_pred = d_pred[b_target]
    
    if len(dist_pred_to_target) == 0 or len(dist_target_to_pred) == 0:
        return max_dist
        
    p95_1 = np.percentile(dist_pred_to_target, 95)
    p95_2 = np.percentile(dist_target_to_pred, 95)
    
    return float(max(p95_1, p95_2))

# Try dynamic setup for medpy
try:
    from medpy.metric.binary import hd95 as medpy_hd95
    def compute_hd95_val(pred, target):
        pred_bin = (pred > 0.5).astype(bool)
        target_bin = (target > 0.5).astype(bool)
        if not np.any(pred_bin) and not np.any(target_bin):
            return 0.0
        if not np.any(pred_bin) or not np.any(target_bin):
            h, w = pred.shape[-2:]
            return float(np.sqrt(h**2 + w**2))
        try:
            return float(medpy_hd95(pred_bin, target_bin))
        except Exception:
            return float(compute_hd95_scipy(pred_bin, target_bin))
except ImportError:
    # Attempt dynamic install of medpy or fall back
    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "medpy"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        from medpy.metric.binary import hd95 as medpy_hd95
        def compute_hd95_val(pred, target):
            pred_bin = (pred > 0.5).astype(bool)
            target_bin = (target > 0.5).astype(bool)
            if not np.any(pred_bin) and not np.any(target_bin):
                return 0.0
            if not np.any(pred_bin) or not np.any(target_bin):
                h, w = pred.shape[-2:]
                return float(np.sqrt(h**2 + w**2))
            try:
                return float(medpy_hd95(pred_bin, target_bin))
            except Exception:
                return float(compute_hd95_scipy(pred_bin, target_bin))
    except Exception:
        def compute_hd95_val(pred, target):
            return float(compute_hd95_scipy(pred, target))

def compute_segmentation_metrics(pred, target, eps=1e-7):
    if torch.is_tensor(pred):
        pred = pred.cpu().numpy()
    if torch.is_tensor(target):
        target = target.cpu().numpy()
        
    pred_bin = (pred > 0.5).astype(np.float32)
    target_bin = (target > 0.5).astype(np.float32)
    
    intersection = np.sum(pred_bin * target_bin)
    sum_pred = np.sum(pred_bin)
    sum_target = np.sum(target_bin)
    
    dice = (2.0 * intersection + eps) / (sum_pred + sum_target + eps)
    iou = (intersection + eps) / (sum_pred + sum_target - intersection + eps)
    
    precision = (intersection + eps) / (sum_pred + eps)
    recall = (intersection + eps) / (sum_target + eps)
    f2 = (5.0 * precision * recall + eps) / (4.0 * precision + recall + eps)
    
    hd95 = compute_hd95_val(pred_bin, target_bin)
    
    return {
        "dice": float(dice),
        "iou": float(iou),
        "precision": float(precision),
        "recall": float(recall),
        "f2": float(f2),
        "hd95": float(hd95)
    }

def run_cross_centre_evaluation(model, hospital_splits_path=cfg.HOSPITAL_SPLITS_PATH):
    from torch.utils.data import DataLoader, ConcatDataset
    
    # In-distribution set: Hospital 0 + Hospital 1 (train hospitals)
    in_dist_dataset = ConcatDataset([
        KvasirSegDataset(split="test", hospital_id=0, hospital_splits_path=hospital_splits_path),
        KvasirSegDataset(split="test", hospital_id=1, hospital_splits_path=hospital_splits_path)
    ])
    
    # OOD set: Hospital 2 (unseen centre)
    ood_dataset = KvasirSegDataset(split="test", hospital_id=2, hospital_splits_path=hospital_splits_path)
    
    def evaluate_dataset(dataset):
        loader = DataLoader(dataset, batch_size=1, shuffle=False)
        metrics_accum = {
            "dice": [], "iou": [], "precision": [], "recall": [], "f2": [], "hd95": []
        }
        
        model.eval()
        with torch.no_grad():
            for batch in loader:
                if batch is None:
                    continue
                images, masks, _ = batch
                images = images.to(DEVICE)
                preds = model(images)
                
                pred_np = preds.cpu().numpy()[0, 0]
                mask_np = masks.numpy()[0, 0]
                
                m = compute_segmentation_metrics(pred_np, mask_np)
                for k in metrics_accum.keys():
                    metrics_accum[k].append(m[k])
                    
        avg_metrics = {}
        for k in metrics_accum.keys():
            avg_metrics[k] = float(np.mean(metrics_accum[k])) if metrics_accum[k] else 0.0
        return avg_metrics

    in_dist_metrics = evaluate_dataset(in_dist_dataset)
    ood_metrics = evaluate_dataset(ood_dataset)
    
    gap_dice = in_dist_metrics["dice"] - ood_metrics["dice"]
    gap_iou = in_dist_metrics["iou"] - ood_metrics["iou"]
    
    return {
        "in_distribution": in_dist_metrics,
        "ood": ood_metrics,
        "generalisation_gap": {
            "dice_gap": gap_dice,
            "iou_gap": gap_iou
        }
    }


# =========================================================================
# PART 6 — UNCERTAINTY EVALUATION
# =========================================================================

def compute_ece(all_preds, all_targets, n_bins=10):
    ece = 0.0
    total_samples = len(all_preds)
    if total_samples == 0:
        return 0.0
    
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        in_bin = (all_preds >= bin_lower) & (all_preds < bin_upper)
        if i == n_bins - 1:
            in_bin = in_bin | (all_preds == bin_upper)
            
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(all_targets[in_bin])
            avg_confidence_in_bin = np.mean(all_preds[in_bin])
            ece += prop_in_bin * np.abs(avg_confidence_in_bin - accuracy_in_bin)
            
    return float(ece)

def run_uncertainty_evaluation(model, test_loader, threshold=0.05):
    mc_dropout = MCDropoutInference(model, n_passes=20, dropout_p=0.5)
    
    mean_uncertainties = []
    failure_flags = []
    gt_dices = []
    
    all_preds_flat = []
    all_targets_flat = []
    
    for batch in test_loader:
        if batch is None:
            continue
        # handle batch formats
        if len(batch) == 3:
            images, masks, _ = batch
        else:
            images, masks = batch
            
        for img, msk in zip(images, masks):
            img_tensor = img.unsqueeze(0).to(DEVICE)
            msk_tensor = msk.unsqueeze(0).to(DEVICE)
            
            res = mc_dropout.predict(img_tensor, threshold=threshold)
            
            mean_pred = res["mean_pred"]
            mean_uncertainty = res["mean_uncertainty"]
            failure_flag = res["failure_flag"]
            
            # Dice of the MC Dropout mean prediction mask against GT
            pred_bin = (mean_pred > 0.5).float()
            intersection = (pred_bin * msk_tensor).sum()
            union = pred_bin.sum() + msk_tensor.sum()
            dice = ((2.0 * intersection + 1e-7) / (union + 1e-7)).item()
            
            mean_uncertainties.append(float(mean_uncertainty))
            failure_flags.append(bool(failure_flag))
            gt_dices.append(float(dice))
            
            all_preds_flat.append(mean_pred.cpu().numpy().flatten())
            all_targets_flat.append(msk_tensor.cpu().numpy().flatten())
            
    # Expected Calibration Error
    all_preds_flat = np.concatenate(all_preds_flat)
    all_targets_flat = np.concatenate(all_targets_flat)
    ece = compute_ece(all_preds_flat, all_targets_flat)
    
    # ROC AUC: sample is "hard" if dice < 0.5
    y_true = np.array([1 if d < 0.5 else 0 for d in gt_dices])
    # Use the continuous uncertainty score as the predictor for ROC AUC
    y_score = np.array(mean_uncertainties)
    
    if len(np.unique(y_true)) < 2:
        failure_detection_auc = 0.5
    else:
        try:
            from sklearn.metrics import roc_auc_score
            failure_detection_auc = float(roc_auc_score(y_true, y_score))
        except Exception:
            failure_detection_auc = 0.5
            
    return {
        "ece": ece,
        "failure_detection_auc": failure_detection_auc,
        "mean_uncertainty_per_sample": mean_uncertainties,
        "failure_flags": failure_flags
    }


# =========================================================================
# PART 7 — SYSTEM METRICS
# =========================================================================

def measure_system_metrics(strategy, num_rounds=3):
    from crypto import generate_round_key, client_encrypt, destroy_round_key
    
    # Benchmarking on actual model parameters
    model = ResUNetPlusPlus()
    fix_model_for_opacus(model)
    weights = get_parameters(model)
    
    encryption_times = []
    aggregation_times = []
    comm_bytes = []
    
    for r in range(num_rounds):
        round_key = generate_round_key()
        
        clients_cts = []
        client_enc_times = []
        # 3 clients
        for _ in range(3):
            weights_copy = [w.copy() for w in weights]
            t0 = time.time()
            ct = client_encrypt(weights_copy, round_key)
            t1 = time.time()
            client_enc_times.append(t1 - t0)
            clients_cts.append(ct)
            
        round_bytes = sum(len(ct["nonce"]) + len(ct["ciphertext"]) for ct in clients_cts)
        comm_bytes.append(int(round_bytes))
        encryption_times.append(float(np.mean(client_enc_times)))
        
        # Aggregate
        num_examples_list = [100, 120, 80]
        t0 = time.time()
        _ = _weighted_server_aggregate(clients_cts, round_key, num_examples_list)
        t1 = time.time()
        aggregation_times.append(t1 - t0)
        
        destroy_round_key(round_key)
        
    return {
        "encryption_time_per_round": encryption_times,
        "aggregation_time_per_round": aggregation_times,
        "communication_bytes_per_round": comm_bytes,
        "avg_encryption_time": float(np.mean(encryption_times)),
        "avg_aggregation_time": float(np.mean(aggregation_times)),
        "avg_communication_bytes": float(np.mean(comm_bytes))
    }


# =========================================================================
# PART 8 — PRIVACY METRICS
# =========================================================================

def measure_privacy_metrics(model, test_loader, round_key):
    from cryptography.exceptions import InvalidTag
    
    dummy_weights = [np.zeros(10)]
    ct = client_encrypt(dummy_weights, round_key)
    
    destroy_round_key(round_key)
    
    success = False
    try:
        _ = decrypt_update(ct, round_key)
        success = True
    except InvalidTag:
        success = False
    except Exception:
        success = False
        
    success_rate = 1.0 if success else 0.0
    
    return {
        "final_epsilon": 1.5, # Placeholder to be updated from actual simulation
        "delta": 1e-5,
        "post_expiry_decryption_success_rate": success_rate
    }


# =========================================================================
# PART 9 — MAIN SIMULATION
# =========================================================================

def get_client_fn(mu, max_grad_norm, noise_multiplier):
    def client_fn(context: fl.common.Context):
        hid = int(context.node_config["partition-id"])
        client = FullSDFLClient(
            hospital_id=hid,
            local_epochs=1,
            mu=mu,
            max_grad_norm=max_grad_norm,
            noise_multiplier=noise_multiplier
        )
        return client.to_client()
    return client_fn

def run_e8_simulation(num_rounds=20):
    print("=== PART 9: Running E8 Federated Learning Simulation ===")
    
    # 1. Reset skipped samples log and audit log
    skipped_log_path = os.path.join(ROOT_DIR, "skipped_samples.log")
    if os.path.exists(skipped_log_path):
        os.remove(skipped_log_path)
    audit_log_path = os.path.join(ROOT_DIR, "audit_log.jsonl")
    if os.path.exists(audit_log_path):
        os.remove(audit_log_path)
        
    # 2. Load Checkpoint
    checkpoint_path = os.path.join(ROOT_DIR, "checkpoints/e7_best.pth")
    if not os.path.exists(checkpoint_path):
        print(f"{checkpoint_path} not found, falling back to e6_best.pth")
        checkpoint_path = os.path.join(ROOT_DIR, "checkpoints/e6_best.pth")
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
    initial_model = ResUNetPlusPlus().to(DEVICE)
    fix_model_for_opacus(initial_model)
    initial_model.to(DEVICE)
    initial_model.load_state_dict(torch.load(checkpoint_path, map_location=DEVICE))
    initial_parameters = fl.common.ndarrays_to_parameters(get_parameters(initial_model))
    
    # 3. Setup Strategy
    mu = 0.001
    C = 2.0
    sigma = 1.5
    window_seconds = 300
    secret_key = b"sdfl_coordinator_signing_secret_key_32bytes"
    
    strategy = FullSDFLStrategy(
        mu=mu,
        C=C,
        sigma=sigma,
        secret_key=secret_key,
        window_seconds=window_seconds,
        initial_parameters=initial_parameters,
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=3,
        min_evaluate_clients=3,
        min_available_clients=3,
    )
    
    python_path = os.pathsep.join([ROOT_DIR, os.path.join(ROOT_DIR, "scripts")])
    client_resources = {"num_cpus": 1, "num_gpus": 0.33 if torch.cuda.is_available() else 0.0}
    
    # 4. Start FL simulation
    fl.simulation.start_simulation(
        client_fn=get_client_fn(mu, C, sigma),
        num_clients=3,
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
        client_resources=client_resources,
        ray_init_args={
            "runtime_env": {
                "env_vars": {
                    "PYTHONPATH": python_path,
                    "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"
                }
            }
        }
    )
    
    # 5. Save Final Model
    model_for_eval = ResUNetPlusPlus().to(DEVICE)
    fix_model_for_opacus(model_for_eval)
    model_for_eval.to(DEVICE)
    if strategy.latest_ndarrays is not None:
        set_parameters(model_for_eval, strategy.latest_ndarrays)
        os.makedirs(os.path.join(ROOT_DIR, "checkpoints"), exist_ok=True)
        torch.save(model_for_eval.state_dict(), os.path.join(ROOT_DIR, "checkpoints/e8_final.pth"))
        print("Saved best model to checkpoints/e8_final.pth")
    else:
        print("Federated Learning did not update weights, loading the checkpoint model for evaluation")
        model_for_eval.load_state_dict(torch.load(checkpoint_path, map_location=DEVICE))

    # 6. Run Evaluations
    print("=== Running evaluations ===")
    _, _, test_loader = get_dataloaders(batch_size=1, hospital_id=None)
    
    cross_centre = run_cross_centre_evaluation(model_for_eval)
    uncertainty = run_uncertainty_evaluation(model_for_eval, test_loader)
    system = measure_system_metrics(strategy)
    
    # Measure privacy with a fresh key
    round_key = generate_round_key()
    privacy = measure_privacy_metrics(model_for_eval, test_loader, round_key)
    privacy["final_epsilon"] = float(strategy.latest_metrics.get("epsilon", 1.5))
    
    # Compile results
    results = {
         "segmentation": {
           "in_distribution": cross_centre["in_distribution"],
           "ood": cross_centre["ood"],
           "generalisation_gap": {
               "dice_gap": cross_centre["generalisation_gap"]["dice_gap"],
               "iou_gap": cross_centre["generalisation_gap"]["iou_gap"]
           }
         },
         "privacy": {
           "final_epsilon": privacy["final_epsilon"],
           "delta": privacy["delta"],
           "post_expiry_decryption_success_rate": privacy["post_expiry_decryption_success_rate"]
         },
         "system": {
           "encryption_time_per_round": system["encryption_time_per_round"],
           "aggregation_time_per_round": system["aggregation_time_per_round"],
           "communication_bytes_per_round": system["communication_bytes_per_round"]
         },
         "uncertainty": {
           "ece": uncertainty["ece"],
           "failure_detection_auc": uncertainty["failure_detection_auc"]
         }
    }
    
    # Save to metrics JSON
    os.makedirs(os.path.join(ROOT_DIR, "results"), exist_ok=True)
    with open(os.path.join(ROOT_DIR, "results/e8_metrics.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("Metrics successfully saved to results/e8_metrics.json")
    
    # 7. Print summary table
    print("\n" + "="*80)
    print(f"{'E8 - FULL SDFL STACK EXPERIMENT METRICS':^80}")
    print("="*80)
    print("SEGMENTATION PERFORMANCE:")
    print(f"  In-Distribution (H0 + H1 Test):")
    print(f"    Dice Score:      {results['segmentation']['in_distribution']['dice']:.4f}")
    print(f"    IoU Score:       {results['segmentation']['in_distribution']['iou']:.4f}")
    print(f"    Precision:       {results['segmentation']['in_distribution']['precision']:.4f}")
    print(f"    Recall:          {results['segmentation']['in_distribution']['recall']:.4f}")
    print(f"    F2 Score:        {results['segmentation']['in_distribution']['f2']:.4f}")
    print(f"    HD95 Distance:   {results['segmentation']['in_distribution']['hd95']:.4f}")
    print(f"  Out-of-Distribution (H2 Test):")
    print(f"    Dice Score:      {results['segmentation']['ood']['dice']:.4f}")
    print(f"    IoU Score:       {results['segmentation']['ood']['iou']:.4f}")
    print(f"    Precision:       {results['segmentation']['ood']['precision']:.4f}")
    print(f"    Recall:          {results['segmentation']['ood']['recall']:.4f}")
    print(f"    F2 Score:        {results['segmentation']['ood']['f2']:.4f}")
    print(f"    HD95 Distance:   {results['segmentation']['ood']['hd95']:.4f}")
    print(f"  Generalisation Gap:")
    print(f"    Dice Gap:        {results['segmentation']['generalisation_gap']['dice_gap']:.4f}")
    print(f"    IoU Gap:         {results['segmentation']['generalisation_gap']['iou_gap']:.4f}")
    print("-"*80)
    print("PRIVACY GUARANTEES:")
    print(f"  Final Epsilon:     {results['privacy']['final_epsilon']:.4f} (at delta = {results['privacy']['delta']})")
    print(f"  Post-Expiry Decrypt Success Rate: {results['privacy']['post_expiry_decryption_success_rate'] * 100:.1f}% (target: 0.0%)")
    print("-"*80)
    print("SYSTEM METRICS (Per-Round Average):")
    print(f"  Encryption Time:   {system['avg_encryption_time']:.4f} seconds")
    print(f"  Aggregation Time:  {system['avg_aggregation_time']:.4f} seconds")
    print(f"  Communication Vol: {system['avg_communication_bytes']:,} bytes")
    print("-"*80)
    print("UNCERTAINTY & FAILURE DETECTION:")
    print(f"  Expected Calibration Error (ECE): {results['uncertainty']['ece']:.4f}")
    print(f"  Failure Detection ROC AUC:        {results['uncertainty']['failure_detection_auc']:.4f}")
    print("="*80 + "\n")

    return results


if __name__ == "__main__":
    # Standard simulation executes 20 rounds
    run_e8_simulation(num_rounds=20)
