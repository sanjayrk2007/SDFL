import os
import sys
import json
import argparse
import numpy as np
import torch
import flwr as fl

# Ensure workspace root is in path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

from crypto import generate_round_key, client_encrypt, server_aggregate
from e2_server import hospital_loaders, DEVICE, ResUNetPlusPlus
from e4_dpsgd import DPSGDHospitalClient, fix_model_for_opacus, get_parameters, set_parameters, weighted_average

# ===========================================================================
# SECURITY DOCUMENTATION:
# This implementation provides "AES-GCM encrypted transport with aggregation-side decryption"
# rather than a full cryptographic secure aggregation protocol (like additive secret sharing).
# The client encrypts model updates using AES-GCM (256-bit key) in transit.
# The server receives only encrypted updates, decrypts them exclusively within the
# aggregation pipeline (in-memory aggregation), and never persists individual plaintext updates.
# ===========================================================================

class SecAggDPSGDHospitalClient(DPSGDHospitalClient):
    def fit(self, parameters, config):
        # 1. Retrieve the round key from the config
        key_hex = config["round_key_hex"]
        round_key = bytes.fromhex(key_hex)

        # 2. Run standard local training using Opacus DP-SGD from the parent class
        weights, num_examples, metrics = super().fit(parameters, config)

        # 3. Encrypt the updated weights using the round key
        ct = client_encrypt(weights, round_key)

        # 4. Clean up plaintext weights from memory immediately to prevent leaking
        del weights
        
        # 5. Convert nonce and ciphertext to hex strings for Flower metric compatibility
        metrics["nonce_hex"] = ct["nonce"].hex()
        metrics["ciphertext_hex"] = ct["ciphertext"].hex()

        # Return dummy parameters for the Flower framework channel
        dummy_weights = [np.zeros(1) for _ in range(len(parameters))]
        return dummy_weights, num_examples, metrics


class CheckpointingSecAgg(fl.server.strategy.FedAvg):
    def __init__(self, mu, C, sigma, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mu = mu
        self.C = C
        self.sigma = sigma
        self.latest_metrics = {}
        self.latest_ndarrays = None
        self.current_round_key = None

    def configure_fit(self, server_round, parameters, client_manager):
        # Generate a fresh key for this round
        self.current_round_key = generate_round_key()
        
        # Get standard FitIns from parent
        fit_configs = super().configure_fit(server_round, parameters, client_manager)
        if fit_configs is not None:
            for client_proxy, fit_ins in fit_configs:
                # Inject the round key hex in the config
                fit_ins.config["round_key_hex"] = self.current_round_key.hex()
        return fit_configs

    def validate_update(self, client_id, fit_res):
        """
        Hook for E7 readiness to validate round certificates and timestamps.
        Returns True if the update is valid, False otherwise.
        """
        # Placeholders for E7 rules:
        # 1. Validate signature
        # 2. Check Tr expiry
        # 3. Check key context match
        return True

    def aggregate_fit(self, server_round, results, failures):
        if not results:
            return None, {}
        
        # Extract the ciphertexts from client metrics
        list_of_ciphertexts = []
        epsilons = []
        for client_proxy, fit_res in results:
            # E7 readiness check: validate update certificate and expiry
            if not self.validate_update(client_proxy.cid, fit_res):
                print(f"Warning: Update from client {client_proxy.cid} was rejected (E7 check).")
                continue

            # Reconstruct bytes from hex strings for metrics serialization compatibility
            nonce = bytes.fromhex(fit_res.metrics["nonce_hex"])
            ciphertext = bytes.fromhex(fit_res.metrics["ciphertext_hex"])
            list_of_ciphertexts.append({
                "nonce": nonce,
                "ciphertext": ciphertext
            })
            if "epsilon" in fit_res.metrics:
                epsilons.append(fit_res.metrics["epsilon"])

        if epsilons:
            self.latest_metrics["epsilon"] = max(epsilons)

        # Decrypt and aggregate the updates using server_aggregate
        aggregated_weights = server_aggregate(list_of_ciphertexts, self.current_round_key)
        
        # Secure key destruction & cached ciphertext cleanup
        list_of_ciphertexts.clear()
        self.current_round_key = None

        # Convert to parameters to return
        params = fl.common.ndarrays_to_parameters(aggregated_weights)
        self.latest_ndarrays = aggregated_weights
        
        return params, {}

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
        client = SecAggDPSGDHospitalClient(
            hid, train_loader, val_loader,
            local_epochs=3, mu=mu,
            max_grad_norm=max_grad_norm,
            noise_multiplier=noise_multiplier
        )
        return client.to_client()
    return client_fn


def run_simulation(mu, C, sigma, initial_parameters, num_rounds=1):
    strategy = CheckpointingSecAgg(
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
    client_resources = {"num_cpus": 4, "num_gpus": 0.0} # Configure to run at most 4 parallel clients to avoid OOM
    if torch.cuda.is_available():
        client_resources["num_gpus"] = 1.0
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
    return strategy.latest_metrics, strategy.latest_ndarrays


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_only", action="store_true", help="Run only the isolation tests")
    parser.add_argument("--rounds", type=int, default=1, help="Number of simulation rounds")
    args = parser.parse_args()

    # 1. Run the isolation tests
    print("=== Running E5 Secure Aggregation Isolation Tests ===")
    key = generate_round_key()
    
    # Test 1: Single element encrypt/decrypt
    dummy = torch.randn(100)
    ct = client_encrypt(dummy, key)
    out = server_aggregate([ct], key)
    assert torch.allclose(dummy, out)
    print("Test 1: Single encrypt/decrypt passed.")

    # Test 2: Encrypted aggregation correctness
    x1 = torch.ones(100)
    x2 = torch.ones(100)
    ct1 = client_encrypt(x1, key)
    ct2 = client_encrypt(x2, key)
    out2 = server_aggregate([ct1, ct2], key)
    assert torch.allclose(out2, torch.ones(100))
    print("Test 2: Encrypted aggregation correctness passed.")
    print("All isolation tests passed successfully!\n")

    if args.test_only:
        return

    # 2. Run the federated learning simulation built on top of E4
    print("=== Running E5 Secure Aggregation Simulation ===")
    os.makedirs("checkpoints", exist_ok=True)
    initial_model = ResUNetPlusPlus().to(DEVICE)
    fix_model_for_opacus(initial_model)
    initial_model.load_state_dict(torch.load("checkpoints/e4_best.pth", map_location=DEVICE))
    initial_model.to(DEVICE)
    initial_parameters = fl.common.ndarrays_to_parameters(get_parameters(initial_model))

    # Parameters from E4 best tradeoff config
    mu = 0.001
    C = 2.0
    sigma = 1.5

    metrics, ndarrays = run_simulation(mu, C, sigma, initial_parameters, num_rounds=args.rounds)

    print("\nSimulation Results:")
    print(f"- val_dice: {metrics.get('val_dice', 0.0):.4f}")
    print(f"- val_iou: {metrics.get('val_iou', 0.0):.4f}")
    print(f"- epsilon (privacy spending): {metrics.get('epsilon', 0.0):.4f}")

    if ndarrays is not None:
        best_model = ResUNetPlusPlus().to(DEVICE)
        fix_model_for_opacus(best_model)
        best_model.to(DEVICE)
        set_parameters(best_model, ndarrays)
        torch.save(best_model.state_dict(), "checkpoints/e5_best.pth")
        print("Saved best E5 model checkpoint to checkpoints/e5_best.pth")


if __name__ == "__main__":
    main()
