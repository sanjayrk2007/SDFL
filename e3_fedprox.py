import os
import sys
import json
import shutil
import argparse
import torch
import flwr as fl

# Ensure workspace root is in path
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


class FedProxHospitalClient(HospitalClient):
    def __init__(self, hospital_id, trainloader, valloader, local_epochs=3, mu=0.0):
        super().__init__(hospital_id, trainloader, valloader, local_epochs)
        self.mu = mu

    def fit(self, parameters, config):
        set_parameters(self.model, parameters)

        # Keep global weights constant on device for the proximal term
        global_model = ResUNetPlusPlus().to(DEVICE)
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

                # Standard Dice + BCE loss
                base_loss = self.loss_fn(preds, masks)

                # Proximal term calculation
                prox_loss = 0.0
                if self.mu > 0.0:
                    for lp, gp in zip(self.model.parameters(), global_model.parameters()):
                        prox_loss += torch.sum((lp - gp) ** 2)

                loss = base_loss + (self.mu / 2.0) * prox_loss
                loss.backward()
                self.optimizer.step()

                total_loss += loss.item()
                n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)
        return (get_parameters(self.model), len(self.trainloader.dataset),
                {"hospital_id": self.hospital_id, "train_loss": avg_loss})


class CheckpointingFedProx(fl.server.strategy.FedAvg):
    def __init__(self, mu, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mu = mu
        self.history = []

    def aggregate_fit(self, server_round, results, failures):
        aggregated = super().aggregate_fit(server_round, results, failures)
        if aggregated is not None:
            params, _ = aggregated
            ndarrays = fl.common.parameters_to_ndarrays(params)
            global_model = ResUNetPlusPlus().to(DEVICE)
            set_parameters(global_model, ndarrays)
            os.makedirs("checkpoints", exist_ok=True)
            # Save checkpoint for this mu
            torch.save(global_model.state_dict(), f"checkpoints/e3_mu_{self.mu}_round_{server_round}.pth")
            self._latest_ndarrays = ndarrays
        return aggregated

    def aggregate_evaluate(self, server_round, results, failures):
        agg_loss, _ = super().aggregate_evaluate(server_round, results, failures)
        per_client = [(r.num_examples, r.metrics) for _, r in results]
        avg_metrics = weighted_average(per_client)

        print(f"[mu={self.mu}] Round {server_round:2d}/20 | val_loss {agg_loss:.4f} | "
              f"val_dice {avg_metrics['val_dice']:.4f} | val_iou {avg_metrics['val_iou']:.4f}")

        self.history.append({"round": server_round, "val_loss": agg_loss,
                             "val_dice": avg_metrics["val_dice"], "val_iou": avg_metrics["val_iou"]})

        with open(f"checkpoints/e3_mu_{self.mu}_history.json", "w") as f:
            json.dump(self.history, f, indent=2)

        return agg_loss, avg_metrics


def get_client_fn(mu):
    def client_fn(context: fl.common.Context):
        hid = int(context.node_config["partition-id"])
        train_loader, val_loader = hospital_loaders[hid]
        client = FedProxHospitalClient(hid, train_loader, val_loader, local_epochs=3, mu=mu)
        return client.to_client()
    return client_fn


def run_simulation(mu, num_rounds=20):
    strategy = CheckpointingFedProx(
        mu=mu,
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=3,
        min_evaluate_clients=3,
        min_available_clients=3,
    )
    print(f"\n--- Starting FedProx Simulation (mu={mu}, rounds={num_rounds}) ---")
    python_path = os.pathsep.join([ROOT_DIR, os.path.join(ROOT_DIR, "scripts")])
    fl.simulation.start_simulation(
        client_fn=get_client_fn(mu),
        num_clients=3,
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
        client_resources={"num_cpus": 1, "num_gpus": 0},
        ray_init_args={
            "runtime_env": {
                "env_vars": {"PYTHONPATH": python_path}
            }
        }
    )
    return strategy.history


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=20, help="Number of training rounds per mu")
    parser.add_argument("--test_only", action="store_true", help="Run a quick test of 1 round with mu=0.0")
    args = parser.parse_args()

    os.makedirs("checkpoints", exist_ok=True)

    if args.test_only:
        print("Running quick test with 1 round...")
        run_simulation(mu=0.0, num_rounds=1)
        return

    mus = [0.0, 0.001, 0.01, 0.1]
    results = {}

    for mu in mus:
        history = run_simulation(mu=mu, num_rounds=args.rounds)
        results[str(mu)] = history

    # Find the best mu and round based on validation Dice score
    best_mu = None
    best_round = None
    best_dice = -1.0

    for mu_str, history in results.items():
        for item in history:
            if item["val_dice"] > best_dice:
                best_dice = item["val_dice"]
                best_mu = float(mu_str)
                best_round = item["round"]

    print("\n=== FedProx Sweep Results Summary ===")
    for mu_str, history in results.items():
        max_dice = max(item["val_dice"] for item in history)
        print(f"mu = {mu_str:5s} | Max val_dice = {max_dice:.4f}")

    print(f"\nBest configuration: mu = {best_mu} at Round {best_round} (val_dice = {best_dice:.4f})")

    # Copy the best model checkpoint to checkpoints/e3_best.pth
    best_checkpoint_path = f"checkpoints/e3_mu_{best_mu}_round_{best_round}.pth"
    target_path = "checkpoints/e3_best.pth"
    if os.path.exists(best_checkpoint_path):
        shutil.copy(best_checkpoint_path, target_path)
        print(f"Saved best model checkpoint to {target_path}")
    else:
        print(f"Warning: Best checkpoint file {best_checkpoint_path} not found.")


if __name__ == "__main__":
    main()
