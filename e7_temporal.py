import os
import sys
import json
import time
import uuid
import shutil
import hashlib
import pickle
import argparse
import numpy as np
import torch
import flwr as fl
from cryptography.exceptions import InvalidTag

# Ensure workspace root is in path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

from crypto import (
    generate_round_key,
    client_encrypt,
    decrypt_update,
    destroy_round_key,
    create_certificate,
    sign_certificate,
    verify_certificate,
    write_audit_log,
    server_aggregate
)
from e2_server import hospital_loaders, DEVICE, ResUNetPlusPlus
from e4_dpsgd import fix_model_for_opacus, get_parameters, set_parameters, weighted_average
from e6_server import SanitizedSecAggDPSGDHospitalClient

SECRET_KEY = b"sdfl_coordinator_signing_secret_key_32bytes"

def compute_model_hash(state_dict):
    """
    Computes a deterministic SHA-256 hash of the global model state dict.
    Moves tensors to CPU and serializes them to ensure cross-device consistency.
    """
    cpu_state = {k: v.cpu() for k, v in state_dict.items()}
    serialized = pickle.dumps(cpu_state)
    return hashlib.sha256(serialized).hexdigest()


class TemporalHospitalClient(SanitizedSecAggDPSGDHospitalClient):
    def fit(self, parameters, config):
        # 1. Retrieve the round key and certificate from config
        key_hex = config["round_key_hex"]
        round_key = bytearray(bytes.fromhex(key_hex)) # Convert to mutable bytearray

        # 2. Reconstruct parameters
        underlying_model = self.model._module if hasattr(self.model, "_module") else self.model
        set_parameters(underlying_model, parameters)
        
        global_model = ResUNetPlusPlus().to("cpu")
        fix_model_for_opacus(global_model)
        set_parameters(global_model, parameters)
        for p in global_model.parameters():
            p.requires_grad = False
            
        self.model.train()
        global_model.eval()
        total_loss, n_batches = 0.0, 0
        from opacus.utils.batch_memory_manager import BatchMemoryManager

        for _ in range(self.local_epochs):
            with BatchMemoryManager(
                data_loader=self.trainloader,
                max_physical_batch_size=4,
                optimizer=self.optimizer
            ) as memory_safe_data_loader:
                for batch in memory_safe_data_loader:
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
                            prox_loss += torch.sum((lp - gp.to(DEVICE)) ** 2)
                    loss = base_loss + (self.mu / 2.0) * prox_loss
                    loss.backward()
                    self.optimizer.step()
                    total_loss += loss.item()
                    n_batches += 1
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
        avg_loss = total_loss / max(n_batches, 1)
        epsilon = self.privacy_engine.get_epsilon(delta=1e-5)
        del global_model
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        # Get plaintext weights
        weights = get_parameters(underlying_model)
        
        # Encrypt the updated weights using the round key
        ct = client_encrypt(weights, round_key)
        
        # WIPE client-side plaintext update buffer in-place immediately after encryption
        for w in weights:
            w.fill(0)
        del weights
        
        # Construct metrics with hex strings and E7 certificate validation fields
        metrics = {
            "hospital_id": self.hospital_id,
            "train_loss": avg_loss,
            "epsilon": epsilon,
            "nonce_hex": ct["nonce"].hex(),
            "ciphertext_hex": ct["ciphertext"].hex(),
            "certificate": config["certificate"],
            "signature": config["signature"],
            "key_context_id": config["key_context_id"]
        }
        
        dummy_weights = [np.zeros(1) for _ in range(len(parameters))]
        return dummy_weights, len(self.trainloader.dataset), metrics


class TemporalCheckpointingSecAgg(fl.server.strategy.FedAvg):
    def __init__(self, mu, C, sigma, secret_key, window_seconds=300, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mu = mu
        self.C = C
        self.sigma = sigma
        self.secret_key = secret_key
        self.window_seconds = window_seconds
        self.latest_metrics = {}
        self.latest_ndarrays = None
        
        self.round_history = []
        self.round_keys = {}            # key_context_id -> bytearray key
        self.cached_ciphertexts = {}    # round_id -> list of ciphertexts
        self.current_key_context_id = None
        self.current_Tr = None
        self.AUDIT_LOG_PATH = "audit_log.jsonl"

    def configure_fit(self, server_round, parameters, client_manager):
        # 1. Ephemeral Key Generation (fresh each round)
        self.current_key_context_id = str(uuid.uuid4())
        round_key = generate_round_key()
        self.round_keys[self.current_key_context_id] = round_key
        
        # 2. Expiry Timestamp Tr
        start_time = time.time()
        self.current_Tr = start_time + self.window_seconds
        
        # 3. Model Hash from actual global model weights
        global_model = ResUNetPlusPlus()
        fix_model_for_opacus(global_model)
        ndarrays = fl.common.parameters_to_ndarrays(parameters)
        try:
            set_parameters(global_model, ndarrays)
        except Exception:
            pass
        model_hash = compute_model_hash(global_model.state_dict())
        
        # 4. Participants (IDs of active clients)
        active_clients = client_manager.sample(num_clients=3)
        participants = [c.cid for c in active_clients]
        
        # 5. Create and Sign Certificate
        cert = create_certificate(
            round_id=server_round,
            model_hash=model_hash,
            participants=participants,
            key_context_id=self.current_key_context_id,
            expiry_timestamp=self.current_Tr
        )
        signature = sign_certificate(cert, self.secret_key)
        
        # Audit Log: round_open
        write_audit_log(self.AUDIT_LOG_PATH, {
            "event": "round_open",
            "round_id": server_round,
            "Tr": self.current_Tr
        })
        
        # 6. Configure Fit Instructions
        fit_configs = super().configure_fit(server_round, parameters, client_manager)
        if fit_configs is not None:
            for client_proxy, fit_ins in fit_configs:
                fit_ins.config["round_key_hex"] = round_key.hex()
                fit_ins.config["certificate"] = json.dumps(cert)
                fit_ins.config["signature"] = signature
                fit_ins.config["key_context_id"] = self.current_key_context_id
                
        return fit_configs

    def validate_update(self, fit_res, current_time=None):
        """
        Aggregator rules:
        Accept update only if:
            1. Certificate HMAC signature is valid
            2. current_time < Tr
            3. update's key_context_id matches certificate
        """
        if current_time is None:
            current_time = time.time()
            
        try:
            cert_str = fit_res.metrics.get("certificate")
            signature = fit_res.metrics.get("signature")
            key_context_id = fit_res.metrics.get("key_context_id")
            
            if not cert_str or not signature or not key_context_id:
                return False, "missing_certificate_fields"
                
            cert = json.loads(cert_str)
            
            # Rule 1: Signature check
            if not verify_certificate(cert, signature, self.secret_key):
                return False, "invalid_signature"
                
            # Rule 2: Expiry check (current_time < Tr)
            if current_time >= cert["expiry_timestamp"]:
                return False, "expired"
                
            # Rule 3: Key context mismatch check
            if key_context_id != cert["key_context_id"] or key_context_id != self.current_key_context_id:
                return False, "mismatch"
                
            return True, "accepted"
        except Exception as e:
            return False, f"validation_error: {str(e)}"

    def aggregate_fit(self, server_round, results, failures):
        current_time = time.time()
        
        # 1. Accept updates only if they satisfy validator rules
        list_of_ciphertexts = []
        epsilons = []
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
            
            if "epsilon" in fit_res.metrics:
                epsilons.append(fit_res.metrics["epsilon"])

        # Cache ciphertexts for this round
        self.cached_ciphertexts[server_round] = list_of_ciphertexts

        if epsilons:
            self.latest_metrics["epsilon"] = max(epsilons)

        # 2. Decrypt & Aggregate
        aggregated_weights = None
        round_key = self.round_keys.get(self.current_key_context_id)
        
        if list_of_ciphertexts and round_key is not None:
            try:
                aggregated_weights = server_aggregate(list_of_ciphertexts, round_key)
            except Exception as e:
                print(f"Decryption / Aggregation failed: {e}")

        # 3. Wipe and destroy ephemeral round key + cached ciphertexts at Tr/aggregation completion
        if round_key is not None:
            destroy_round_key(round_key)
            self.round_keys.pop(self.current_key_context_id, None)
            
        self.cached_ciphertexts.pop(server_round, None)
        list_of_ciphertexts.clear()
        
        # Audit Logs: round_close & key_destroyed
        t_now = time.time()
        write_audit_log(self.AUDIT_LOG_PATH, {
            "event": "round_close",
            "round_id": server_round,
            "timestamp": t_now
        })
        write_audit_log(self.AUDIT_LOG_PATH, {
            "event": "key_destroyed",
            "round_id": server_round,
            "timestamp": t_now
        })

        if aggregated_weights is None:
            return None, {}

        # Convert and return parameters
        params = fl.common.ndarrays_to_parameters(aggregated_weights)
        self.latest_ndarrays = aggregated_weights
        
        return params, {}

    def aggregate_evaluate(self, server_round, results, failures):
        agg_loss, _ = super().aggregate_evaluate(server_round, results, failures)
        if not results:
            return agg_loss, {}
        per_client = [(r.num_examples, r.metrics) for _, r in results]
        avg_metrics = weighted_average(per_client)
        if avg_metrics is not None:
            self.latest_metrics["val_dice"] = avg_metrics.get("val_dice", 0.0)
            self.latest_metrics["val_iou"] = avg_metrics.get("val_iou", 0.0)
            
            val_dice = avg_metrics.get("val_dice", 0.0)
            val_iou = avg_metrics.get("val_iou", 0.0)
            loss_val = agg_loss if agg_loss is not None else 0.0
            self.round_history.append((server_round, val_dice, val_iou, loss_val))
            print(f"Round {server_round:2d}/20 | val_loss {loss_val:.4f} | "
                  f"val_dice {val_dice:.4f} | val_iou {val_iou:.4f}")
        return agg_loss, avg_metrics


def get_client_fn(mu, max_grad_norm, noise_multiplier):
    def client_fn(context: fl.common.Context):
        hid = int(context.node_config["partition-id"])
        client = TemporalHospitalClient(
            hospital_id=hid,
            local_epochs=1, mu=mu,
            max_grad_norm=max_grad_norm,
            noise_multiplier=noise_multiplier
        )
        return client.to_client()
    return client_fn


def run_e7_simulation(num_rounds=1):
    # 1. Reset skipped samples log
    log_path = "skipped_samples.log"
    if os.path.exists(log_path):
        os.remove(log_path)

    # 2. Load E6 best checkpoint
    initial_model = ResUNetPlusPlus().to(DEVICE)
    fix_model_for_opacus(initial_model)
    initial_model.to(DEVICE)
    checkpoint_path = "checkpoints/e6_best.pth"
    if not os.path.exists(checkpoint_path):
        print("checkpoints/e6_best.pth not found, falling back to checkpoints/e5_best.pth")
        checkpoint_path = "checkpoints/e5_best.pth"
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    initial_model.load_state_dict(torch.load(checkpoint_path, map_location=DEVICE))
    initial_parameters = fl.common.ndarrays_to_parameters(get_parameters(initial_model))

    # Configure Strategy
    mu = 0.001
    C = 2.0
    sigma = 1.5

    strategy = TemporalCheckpointingSecAgg(
        mu=mu,
        C=C,
        sigma=sigma,
        secret_key=SECRET_KEY,
        window_seconds=7200,
        initial_parameters=initial_parameters,
        fraction_fit=1.0,
        fraction_evaluate=1.0,
        min_fit_clients=3,
        min_evaluate_clients=3,
        min_available_clients=3,
    )

    python_path = os.pathsep.join([ROOT_DIR, os.path.join(ROOT_DIR, "scripts")])
    client_resources = {"num_cpus": 4, "num_gpus": 0.0}
    if torch.cuda.is_available():
        client_resources["num_gpus"] = 1.0

    print("Starting E7 Federated Learning simulation...")
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

    # Save model to checkpoints/e7_best.pth
    if strategy.latest_ndarrays is not None:
        best_model = ResUNetPlusPlus().to(DEVICE)
        fix_model_for_opacus(best_model)
        set_parameters(best_model, strategy.latest_ndarrays)
        os.makedirs("checkpoints", exist_ok=True)
        torch.save(best_model.state_dict(), "checkpoints/e7_best.pth")
        print("Saved best model to checkpoints/e7_best.pth")

    return strategy.latest_metrics


def run_e7_tests():
    print("=== Running E7 Temporal Key Destruction Verification Tests ===")
    import time
    import uuid
    import json
    import torch
    from cryptography.exceptions import InvalidTag
    from crypto import (
        generate_round_key,
        client_encrypt,
        decrypt_update,
        destroy_round_key,
        create_certificate,
        sign_certificate,
        write_audit_log,
        verify_certificate
    )
    
    SECRET_KEY_TEST = b"test_coordinator_secret_key_32bytes"
    AUDIT_LOG_PATH = "test_audit_log.jsonl"
    if os.path.exists(AUDIT_LOG_PATH):
        os.remove(AUDIT_LOG_PATH)
        
    # Setup test strategy and certificate
    round_id = 1
    key_context_id = str(uuid.uuid4())
    expiry_timestamp = time.time() + 10  # Tr is 10s in the future
    participants = ["client0", "client1", "client2"]
    model_hash = "dummy_model_hash_sha256"
    
    cert = create_certificate(
        round_id=round_id,
        model_hash=model_hash,
        participants=participants,
        key_context_id=key_context_id,
        expiry_timestamp=expiry_timestamp
    )
    signature = sign_certificate(cert, SECRET_KEY_TEST)
    
    # Test 1: Submit update at Tr - 1s -> accepted
    print("Running Test 1: Submit update at Tr - 1s...")
    strategy = TemporalCheckpointingSecAgg(
        mu=0.001, C=2.0, sigma=1.5, secret_key=SECRET_KEY_TEST, window_seconds=10
    )
    strategy.current_key_context_id = key_context_id
    strategy.current_Tr = expiry_timestamp
    strategy.AUDIT_LOG_PATH = AUDIT_LOG_PATH
    
    # Simulate client update metrics
    key = generate_round_key()
    strategy.round_keys[key_context_id] = key
    dummy_weights = torch.ones(10)
    ct = client_encrypt(dummy_weights, key)
    
    fit_res_metrics = {
        "nonce_hex": ct["nonce"].hex(),
        "ciphertext_hex": ct["ciphertext"].hex(),
        "certificate": json.dumps(cert),
        "signature": signature,
        "key_context_id": key_context_id
    }
    
    class DummyClientProxy:
        def __init__(self, cid):
            self.cid = cid
            
    class DummyFitRes:
        def __init__(self, metrics):
            self.metrics = metrics
            
    client_proxy = DummyClientProxy("client0")
    fit_res = DummyFitRes(fit_res_metrics)
    
    # Validate at Tr - 1s
    is_valid, reason = strategy.validate_update(fit_res, current_time=expiry_timestamp - 1.0)
    assert is_valid, f"Test 1 failed: update should be accepted, but got: {reason}"
    print("Test 1 passed: Update at Tr - 1s accepted.")

    # Test 2: Submit update at Tr + 1s -> rejected with "expired"
    print("Running Test 2: Submit update at Tr + 1s...")
    is_valid, reason = strategy.validate_update(fit_res, current_time=expiry_timestamp + 1.0)
    assert not is_valid and reason == "expired", f"Test 2 failed: expected 'expired', got {reason}"
    print("Test 2 passed: Update at Tr + 1s rejected with 'expired'.")

    # Test 3: Submit update with wrong key_context_id -> rejected with "mismatch"
    print("Running Test 3: Submit update with wrong key_context_id...")
    wrong_fit_res_metrics = fit_res_metrics.copy()
    wrong_fit_res_metrics["key_context_id"] = str(uuid.uuid4())
    wrong_fit_res = DummyFitRes(wrong_fit_res_metrics)
    is_valid, reason = strategy.validate_update(wrong_fit_res, current_time=expiry_timestamp - 1.0)
    assert not is_valid and reason == "mismatch", f"Test 3 failed: expected 'mismatch', got {reason}"
    print("Test 3 passed: Update with wrong key_context_id rejected with 'mismatch'.")

    # Test 4: After Tr, attempt decryption with round key -> raises InvalidTag
    print("Running Test 4: Post-expiry decryption attempt must fail...")
    # Overwrite the key bytearray in-place with zeroes to simulate destruction
    destroy_round_key(key)
    try:
        decrypt_update(ct, key)
        raise AssertionError("Test 4 failed: Decryption succeeded with destroyed key!")
    except InvalidTag:
        print("Test 4 passed: Attempted decryption with destroyed key raised InvalidTag.")

    # Test 5: audit_log.jsonl contains all 3 event types after round closes
    print("Running Test 5: Verify audit log entries...")
    class DummyClientManager:
        def sample(self, num_clients, min_num_clients=None):
            return [DummyClientProxy("client0"), DummyClientProxy("client1"), DummyClientProxy("client2")]
        def num_available(self):
            return 3
            
    test_model = ResUNetPlusPlus()
    fix_model_for_opacus(test_model)
    test_params = fl.common.ndarrays_to_parameters(get_parameters(test_model))
    
    # Configure the strategy
    fit_configs = strategy.configure_fit(server_round=1, parameters=test_params, client_manager=DummyClientManager())
    client_config = fit_configs[0][1].config
    
    cert_str = client_config["certificate"]
    sig = client_config["signature"]
    ctx_id = client_config["key_context_id"]
    key_hex = client_config["round_key_hex"]
    
    # Encrypt the dummy weights using the generated round key
    round_key = bytearray(bytes.fromhex(key_hex))
    fresh_ct = client_encrypt(dummy_weights, round_key)
    
    fresh_fit_res_metrics = {
        "nonce_hex": fresh_ct["nonce"].hex(),
        "ciphertext_hex": fresh_ct["ciphertext"].hex(),
        "certificate": cert_str,
        "signature": sig,
        "key_context_id": ctx_id
    }
    fit_results = [(client_proxy, DummyFitRes(fresh_fit_res_metrics))]
    
    strategy.aggregate_fit(server_round=1, results=fit_results, failures=[])
    
    with open(AUDIT_LOG_PATH, "r") as f:
        log_lines = f.readlines()
        
    events = [json.loads(line.strip())["event"] for line in log_lines]
    print(f"Log events found: {events}")
    assert "round_open" in events, "Missing round_open in audit log"
    assert "round_close" in events, "Missing round_close in audit log"
    assert "key_destroyed" in events, "Missing key_destroyed in audit log"
    print("Test 5 passed: All 3 event types present in audit log.")
    
    if os.path.exists(AUDIT_LOG_PATH):
        os.remove(AUDIT_LOG_PATH)
        
    print("All E7 verification tests passed successfully!\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_only", action="store_true", help="Run only the E7 tests")
    parser.add_argument("--rounds", type=int, default=1, help="Number of FL rounds to run")
    args = parser.parse_args()

    # 1. Run the 5 verification tests
    run_e7_tests()

    if args.test_only:
        return

    # 2. Run simulation
    run_e7_simulation(num_rounds=args.rounds)


if __name__ == "__main__":
    main()
