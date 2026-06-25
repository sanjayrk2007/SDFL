import os
import sys
import json
import shutil
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import flwr as fl
from opacus import PrivacyEngine

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

from e2_server import (
    HospitalClient,
    get_parameters,
    set_parameters,
    weighted_average,
    hospital_loaders,
    DEVICE,
    ResUNetPlusPlus,
    DiceBCELoss
)

def convert_bn_to_gn(model, num_groups=4):
    for name, module in model.named_children():
        if isinstance(module, nn.BatchNorm2d):
            device = module.weight.device if module.weight is not None else torch.device("cpu")
            gn = nn.GroupNorm(num_groups=num_groups, num_channels=module.num_features).to(device)
            if module.weight is not None:
                gn.weight.data.copy_(module.weight.data)
            if module.bias is not None:
                gn.bias.data.copy_(module.bias.data)
            setattr(model, name, gn)
        else:
            convert_bn_to_gn(module, num_groups)

def disable_inplace_relu(model):
    for name, module in model.named_children():
        if isinstance(module, nn.ReLU):
            module.inplace = False
        else:
            disable_inplace_relu(module)

def fix_model_for_opacus(model):
    convert_bn_to_gn(model, num_groups=4)
    disable_inplace_relu(model)

def dice_iou_score(pred, target, eps=1e-7):
    pred_bin = (pred > 0.5).float()
    intersection = (pred_bin * target).sum(dim=(1, 2, 3))
    union = pred_bin.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3))
    dice = (2 * intersection + eps) / (union + eps)
    iou = (intersection + eps) / (union - intersection + eps)
    return dice.mean().item(), iou.mean().item()

class DPSGDHospitalClient(HospitalClient):
    def __init__(self, hospital_id, trainloader, valloader, local_epochs=3, mu=0.0, max_grad_norm=1.0, noise_multiplier=1.0):
        self.hospital_id = hospital_id
        self.model = ResUNetPlusPlus().to(DEVICE)
        fix_model_for_opacus(self.model)
        self.model.to(DEVICE)
        self.trainloader = trainloader
        self.valloader = valloader
        self.local_epochs = local_epochs
        self.loss_fn = DiceBCELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-4)
        self.mu = mu
        self.max_grad_norm = max_grad_norm
        self.noise_multiplier = noise_multiplier
        self.privacy_engine = PrivacyEngine()
        self.model, self.optimizer, self.trainloader = self.privacy_engine.make_private(
            module=self.model,
            optimizer=self.optimizer,
            data_loader=self.trainloader,
            noise_multiplier=self.noise_multiplier,
            max_grad_norm=self.max_grad_norm,
        )

    def fit(self, parameters, config):
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
            for images, masks, _ in self.trainloader:
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
        return (get_parameters(underlying_model), len(self.trainloader.dataset),
                {"hospital_id": self.hospital_id, "train_loss": avg_loss, "epsilon": epsilon})

    def evaluate(self, parameters, config):
        underlying_model = self.model._module if hasattr(self.model, "_module") else self.model
        set_parameters(underlying_model, parameters)
        self.model.eval()
        total_loss, total_dice, total_iou, n_batches = 0.0, 0.0, 0.0, 0
        with torch.no_grad():
            for images, masks, _ in self.valloader:
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

class CheckpointingDPSGD(fl.server.strategy.FedAvg):
    def __init__(self, C, sigma, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.C = C
        self.sigma = sigma
        self.latest_metrics = {}
        self.latest_ndarrays = None

    def aggregate_fit(self, server_round, results, failures):
        aggregated = super().aggregate_fit(server_round, results, failures)
        epsilons = [r.metrics["epsilon"] for _, r in results if "epsilon" in r.metrics]
        if epsilons:
            self.latest_metrics["epsilon"] = max(epsilons)
        if aggregated is not None and aggregated[0] is not None:
            params, _ = aggregated
            self.latest_ndarrays = fl.common.parameters_to_ndarrays(params)
        return aggregated

    def aggregate_evaluate(self, server_round, results, failures):
        agg_loss, _ = super().aggregate_evaluate(server_round, results, failures)
        per_client = [(r.num_examples, r.metrics) for _, r in results]
        avg_metrics = weighted_average(per_client)
        self.latest_metrics["val_dice"] = avg_metrics["val_dice"]
        self.latest_metrics["val_iou"] = avg_metrics["val_iou"]
        return agg_loss, avg_metrics

def get_client_fn(mu, max_grad_norm, noise_multiplier):
    def client_fn(context: fl.common.Context):
        hid = int(context.node_config["partition-id"])
        train_loader, val_loader = hospital_loaders[hid]
        client = DPSGDHospitalClient(
            hid, train_loader, val_loader,
            local_epochs=3, mu=mu,
            max_grad_norm=max_grad_norm,
            noise_multiplier=noise_multiplier
        )
        return client.to_client()
    return client_fn

def run_simulation(mu, C, sigma, initial_parameters):
    strategy = CheckpointingDPSGD(
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
    client_resources = {"num_cpus": 1, "num_gpus": 0.0}
    if torch.cuda.is_available():
        client_resources["num_gpus"] = 1.0
    fl.simulation.start_simulation(
        client_fn=get_client_fn(mu, C, sigma),
        num_clients=3,
        config=fl.server.ServerConfig(num_rounds=1),
        strategy=strategy,
        client_resources=client_resources,
        ray_init_args={
            "runtime_env": {
                "env_vars": {"PYTHONPATH": python_path}
            }
        }
    )
    return strategy.latest_metrics, strategy.latest_ndarrays

def main():
    os.makedirs("checkpoints", exist_ok=True)
    initial_model = ResUNetPlusPlus().to(DEVICE)
    initial_model.load_state_dict(torch.load("checkpoints/e3_best.pth", map_location=DEVICE))
    fix_model_for_opacus(initial_model)
    initial_model.to(DEVICE)
    initial_parameters = fl.common.ndarrays_to_parameters(get_parameters(initial_model))
    mu = 0.001
    sweep_results = []
    best_score = -1.0
    best_params = None
    best_ndarrays = None
    for C in [0.5, 1.0, 2.0]:
        for sigma in [0.5, 1.0, 1.5]:
            metrics, ndarrays = run_simulation(mu, C, sigma, initial_parameters)
            val_dice = metrics.get("val_dice", 0.0)
            val_iou = metrics.get("val_iou", 0.0)
            epsilon = metrics.get("epsilon", 0.0)
            sweep_results.append({
                "C": C,
                "sigma": sigma,
                "val_dice": val_dice,
                "val_iou": val_iou,
                "epsilon": epsilon
            })
            score = val_dice / (epsilon + 1e-5)
            if score > best_score:
                best_score = score
                best_params = (C, sigma, val_dice, val_iou, epsilon)
                best_ndarrays = ndarrays
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            import gc
            gc.collect()
    print("Sweep Results:")
    print("| C   | \u03c3   | val_dice | val_iou | epsilon |")
    print("|-----|-----|----------|---------|---------|")
    for res in sweep_results:
        print(f"| {res['C']:.1f} | {res['sigma']:.1f} | {res['val_dice']:.4f} | {res['val_iou']:.4f} | {res['epsilon']:.4f} |")
    if best_ndarrays is not None:
        best_model = ResUNetPlusPlus().to(DEVICE)
        fix_model_for_opacus(best_model)
        best_model.to(DEVICE)
        set_parameters(best_model, best_ndarrays)
        torch.save(best_model.state_dict(), "checkpoints/e4_best.pth")
    print("Best Configuration:")
    print(f"- C: {best_params[0]:.1f}")
    print(f"- \u03c3: {best_params[1]:.1f}")
    print(f"- val_dice: {best_params[2]:.4f}")
    print(f"- val_iou: {best_params[3]:.4f}")
    print(f"- epsilon: {best_params[4]:.4f}")
    print(f"- delta: 1e-5")

if __name__ == "__main__":
    main()
