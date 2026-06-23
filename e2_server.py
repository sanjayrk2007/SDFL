import os
import sys
import json
import subprocess
from collections import OrderedDict
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import flwr as fl

# Ensure workspace root and scripts folder are in PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

from model import ResUNetPlusPlus
from losses import DiceBCELoss
from dataset import KvasirSegDataset

# Device configuration
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

hospital_loaders = {}
for hid in range(3):
    h_train = KvasirSegDataset(split="train", hospital_id=hid)
    h_val = KvasirSegDataset(split="val", hospital_id=hid)
    h_train_loader = DataLoader(h_train, batch_size=8, shuffle=True)
    h_val_loader = DataLoader(h_val, batch_size=8, shuffle=False)
    hospital_loaders[hid] = (h_train_loader, h_val_loader)


def get_parameters(model):
    return [val.cpu().numpy() for _, val in model.state_dict().items()]


def set_parameters(model, parameters):
    params_dict = zip(model.state_dict().keys(), parameters)
    state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
    model.load_state_dict(state_dict, strict=True)


def dice_iou_score(pred, target, eps=1e-7):
    pred_bin = (pred > 0.5).float()
    intersection = (pred_bin * target).sum(dim=(1, 2, 3))
    union = pred_bin.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3))
    dice = (2 * intersection + eps) / (union + eps)
    iou = (intersection + eps) / (union - intersection + eps)
    return dice.mean().item(), iou.mean().item()


class HospitalClient(fl.client.NumPyClient):
    def __init__(self, hospital_id, trainloader, valloader, local_epochs=3):
        self.hospital_id = hospital_id
        self.model = ResUNetPlusPlus().to(DEVICE)
        self.trainloader = trainloader
        self.valloader = valloader
        self.local_epochs = local_epochs
        self.loss_fn = DiceBCELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-4)

    def get_parameters(self, config):
        return get_parameters(self.model)

    def fit(self, parameters, config):
        set_parameters(self.model, parameters)
        self.model.train()

        total_loss, n_batches = 0.0, 0
        for _ in range(self.local_epochs):
            for images, masks, _ in self.trainloader:
                images, masks = images.to(DEVICE), masks.to(DEVICE)
                self.optimizer.zero_grad()
                preds = self.model(images)
                loss = self.loss_fn(preds, masks)
                loss.backward()
                self.optimizer.step()
                total_loss += loss.item()
                n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)
        return (get_parameters(self.model), len(self.trainloader.dataset),
                {"hospital_id": self.hospital_id, "train_loss": avg_loss})

    def evaluate(self, parameters, config):
        set_parameters(self.model, parameters)
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
        return (avg_loss, len(self.valloader.dataset),
                {"hospital_id": self.hospital_id, "val_dice": avg_dice, "val_iou": avg_iou})


def client_fn(context: fl.common.Context):
    hid = int(context.node_config["partition-id"])
    train_loader, val_loader = hospital_loaders[hid]
    client = HospitalClient(hid, train_loader, val_loader, local_epochs=3)
    return client.to_client()


e2_history = []


def push_checkpoint(round_num):
    username = os.environ.get("GITHUB_USERNAME")
    token = os.environ.get("GITHUB_TOKEN")
    if not username or not token:
        return
    remote_url = f"https://{username}:{token}@github.com/sanjayrk2007/SDFL.git"
    subprocess.run(["git", "add", f"checkpoints/e2_round_{round_num}.pth", "checkpoints/e2_history.json"], cwd=ROOT_DIR)
    subprocess.run(["git", "config", "user.email", "you@example.com"], cwd=ROOT_DIR)
    subprocess.run(["git", "config", "user.name", username], cwd=ROOT_DIR)
    subprocess.run(["git", "commit", "-m", f"E2 round {round_num} checkpoint"], cwd=ROOT_DIR)
    subprocess.run(["git", "push", remote_url, "main"], cwd=ROOT_DIR)


def weighted_average(metrics):
    dices = [m["val_dice"] * n for n, m in metrics]
    ious = [m["val_iou"] * n for n, m in metrics]
    total_n = sum(n for n, _ in metrics)
    return {"val_dice": sum(dices) / total_n, "val_iou": sum(ious) / total_n}


class CheckpointingFedAvg(fl.server.strategy.FedAvg):
    def aggregate_fit(self, server_round, results, failures):
        aggregated = super().aggregate_fit(server_round, results, failures)
        if aggregated is not None:
            params, _ = aggregated
            ndarrays = fl.common.parameters_to_ndarrays(params)
            global_model = ResUNetPlusPlus().to(DEVICE)
            set_parameters(global_model, ndarrays)
            os.makedirs("checkpoints", exist_ok=True)
            torch.save(global_model.state_dict(), f"checkpoints/e2_round_{server_round}.pth")
            self._latest_ndarrays = ndarrays
        return aggregated

    def aggregate_evaluate(self, server_round, results, failures):
        agg_loss, _ = super().aggregate_evaluate(server_round, results, failures)
        per_client = [(r.num_examples, r.metrics) for _, r in results]
        avg_metrics = weighted_average(per_client)

        print(f"Round {server_round:2d}/20 | val_loss {agg_loss:.4f} | "
              f"val_dice {avg_metrics['val_dice']:.4f} | val_iou {avg_metrics['val_iou']:.4f}")

        e2_history.append({"round": server_round, "val_loss": agg_loss,
                            "val_dice": avg_metrics["val_dice"], "val_iou": avg_metrics["val_iou"]})

        with open("checkpoints/e2_history.json", "w") as f:
            json.dump(e2_history, f, indent=2)

        push_checkpoint(server_round)

        return agg_loss, avg_metrics


if __name__ == "__main__":
    strategy = CheckpointingFedAvg(
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=3,
        min_evaluate_clients=3,
        min_available_clients=3,
    )
    print("Starting FedAvg simulation...")
    python_path = os.pathsep.join([ROOT_DIR, os.path.join(ROOT_DIR, "scripts")])
    fl.simulation.start_simulation(
        client_fn=client_fn,
        num_clients=3,
        config=fl.server.ServerConfig(num_rounds=20),
        strategy=strategy,
        client_resources={"num_cpus": 1, "num_gpus": 0},
        ray_init_args={
            "runtime_env": {
                "env_vars": {"PYTHONPATH": python_path}
            }
        }
    )
