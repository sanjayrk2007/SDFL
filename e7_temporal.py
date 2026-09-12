import os
import sys
import json
import time
import uuid
import shutil
import hashlib
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
    Computes a deterministic SHA-256 hash of a model state_dict.
    Hashes key names, dtypes, shapes, and raw contiguous CPU bytes in sorted key order.
    Does NOT use pickle.
    """
    hasher = hashlib.sha256()
    for k in sorted(state_dict.keys()):
        tensor = state_dict[k]
        cpu_tensor = tensor.detach().cpu()
        arr = cpu_tensor.numpy()
        if not arr.flags['C_CONTIGUOUS']:
            arr = np.ascontiguousarray(arr)

        hasher.update(k.encode('utf-8'))
        hasher.update(str(arr.dtype).encode('ascii'))
        hasher.update(str(arr.shape).encode('ascii'))
        hasher.update(arr.tobytes())

    return hasher.hexdigest()


def compute_aad(round_id, client_id, model_hash, key_context_id) -> bytes:
    """
    Computes a canonical, deterministic AAD payload for AES-GCM encryption.
    Binds security metadata without containing secrets.
    """
    aad_dict = {
        "round_id": round_id,
        "client_id": str(client_id),
        "model_hash": str(model_hash),
        "key_context_id": str(key_context_id)
    }
    return json.dumps(aad_dict, sort_keys=True).encode('utf-8')


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

        # 3. Construct Client Certificate and AAD
        cert_str = config["certificate"]
        cert = json.loads(cert_str)
        client_id = f"client{self.hospital_id}" if isinstance(self.hospital_id, int) else str(self.hospital_id)
        cert["client_id"] = client_id

        # Compute AAD over round metadata
        aad = compute_aad(
            cert["round_id"],
            client_id,
            cert["model_hash"],
            cert["key_context_id"]
        )

        # Encrypt the updated weights using the round key and AAD
        ct = client_encrypt(weights, round_key, associated_data=aad)

        destroy_round_key(round_key)

        # Compute update hash over ciphertext + nonce
        update_hash = hashlib.sha256(ct["nonce"] + ct["ciphertext"]).hexdigest()
        cert["update_hash"] = update_hash

        # Re-sign the client certificate with update_hash and client_id bound
        signature = sign_certificate(cert, SECRET_KEY)

        # WIPE client-side plaintext update buffer in-place immediately after encryption
        for w in weights:
            w.fill(0)
        del weights

        # Clear gradients on underlying model for memory hygiene
        if hasattr(self, "optimizer") and self.optimizer is not None:
            self.optimizer.zero_grad(set_to_none=True)
        for p in underlying_model.parameters():
            if p.grad is not None:
                p.grad.detach_().zero_()

        # Construct metrics with hex strings and E7 certificate validation fields
        metrics = {
            "hospital_id": self.hospital_id,
            "train_loss": avg_loss,
            "epsilon": epsilon,
            "nonce_hex": ct["nonce"].hex(),
            "ciphertext_hex": ct["ciphertext"].hex(),
            "certificate": json.dumps(cert),
            "signature": signature,
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
        self.seen_updates = {}          # round_id -> set of (client_id, update_hash)
        self.current_key_context_id = None
        self.current_Tr = None
        self.current_model_hash = None
        self.AUDIT_LOG_PATH = "audit_log.jsonl"

    def configure_fit(self, server_round, parameters, client_manager):
        # 1. Ephemeral Key Generation (fresh each round)
        self.current_key_context_id = str(uuid.uuid4())
        round_key = generate_round_key()
        self.round_keys[self.current_key_context_id] = round_key

        # 2. Expiry Timestamp Tr
        start_time = time.time()
        self.current_Tr = start_time + self.window_seconds

        # 3. Model Hash from actual global model weights using deterministic hash
        global_model = ResUNetPlusPlus()
        fix_model_for_opacus(global_model)
        ndarrays = fl.common.parameters_to_ndarrays(parameters)
        try:
            set_parameters(global_model, ndarrays)
        except Exception as e:
            import logging
            logging.warning(f"Could not load state dict in configure_fit: {e}")
        self.current_model_hash = compute_model_hash(global_model.state_dict())

        # 4. Participants: SDFL logical client identities.
        # Flower cids are runtime identifiers and must not be used as
        # the protocol-level client identities.
        active_clients = client_manager.sample(num_clients=3)
        participants = [f"client{i}" for i in range(len(active_clients))]

        # 5. Create and Sign Certificate Template
        cert = create_certificate(
            round_id=server_round,
            model_hash=self.current_model_hash,
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

    def validate_update(self, fit_res, client_proxy=None, current_time=None):
        """
        Aggregator rules:
        Accept update only if:
            1. Certificate HMAC signature is valid
            2. current_time < Tr
            3. update's key_context_id matches certificate and current round
            4. model_hash matches current global model hash
            5. update_hash matches SHA-256(nonce + ciphertext)
            6. client_id matches submitting client ID (if available)
            7. update has not been seen before in this round (replay protection)
        """
        # Positional parameter signature adaptation for compatibility
        if isinstance(client_proxy, (float, int)) and current_time is None:
            current_time = client_proxy
            client_proxy = None

        if current_time is None:
            current_time = time.time()

        try:
            cert_str = fit_res.metrics.get("certificate")
            signature = fit_res.metrics.get("signature")
            key_context_id = fit_res.metrics.get("key_context_id")
            nonce_hex = fit_res.metrics.get("nonce_hex")
            ciphertext_hex = fit_res.metrics.get("ciphertext_hex")

            if not cert_str or not signature or not key_context_id or not nonce_hex or not ciphertext_hex:
                return False, "missing_certificate_fields"

            cert = json.loads(cert_str)

            # Rule 1: Signature check
            if not verify_certificate(cert, signature, self.secret_key):
                return False, "invalid_signature"

            # Rule 2: Expiry check (current_time < Tr)
            if current_time >= cert["expiry_timestamp"]:
                return False, "expired"

            # Rule 3: Key context mismatch check
            if key_context_id != cert.get("key_context_id") or (self.current_key_context_id is not None and key_context_id != self.current_key_context_id):
                return False, "mismatch"

            # Rule 4: Model hash mismatch check
            if self.current_model_hash is not None and cert.get("model_hash") != self.current_model_hash:
                return False, "model_hash_mismatch"

            # Rule 5: Update hash check (if present in cert)
            nonce = bytes.fromhex(nonce_hex)
            ciphertext = bytes.fromhex(ciphertext_hex)
            computed_update_hash = hashlib.sha256(nonce + ciphertext).hexdigest()
            if "update_hash" in cert and cert["update_hash"] != computed_update_hash:
                return False, "update_hash_mismatch"

            # Rule 6: Validate SDFL logical client identity.
            # hospital_id is the stable application-level identity; Flower's
            # client_proxy.cid is only a runtime transport identifier.
            cert_client_id = cert.get("client_id")
            hospital_id = fit_res.metrics.get("hospital_id")

            if cert_client_id is None or hospital_id is None:
                return False, "missing_client_identity"

            expected_client_id = f"client{hospital_id}"
            if cert_client_id != expected_client_id:
                return False, "wrong_client_id"

            # The logical client must also be an authorized participant
            # for this round.
            participants = cert.get("participants", [])
            if cert_client_id not in participants:
                return False, "unauthorized_client"

            # Rule 7: Replay protection check
            round_id = cert.get("round_id", 1)
            replay_key = (cert_client_id, computed_update_hash)
            round_seen = self.seen_updates.setdefault(round_id, set())
            if replay_key in round_seen:
                return False, "replay_detected"

            round_seen.add(replay_key)
            return True, "accepted"
        except Exception as e:
            return False, f"validation_error: {str(e)}"

    def aggregate_fit(self, server_round, results, failures):
        current_time = time.time()
        list_of_ciphertexts = []
        epsilons = []
        num_examples_list = []

        try:
            # 1. Accept updates only if they satisfy validator rules
            for client_proxy, fit_res in results:
                is_valid, reason = self.validate_update(fit_res, client_proxy=client_proxy, current_time=current_time)
                if not is_valid:
                    print(f"Aggregator rejected update from client {client_proxy.cid if hasattr(client_proxy, 'cid') else 'unknown'}: {reason}")
                    continue

                nonce = bytes.fromhex(fit_res.metrics["nonce_hex"])
                ciphertext = bytes.fromhex(fit_res.metrics["ciphertext_hex"])
                cert = json.loads(fit_res.metrics["certificate"])

                # Reconstruct AAD
                aad = compute_aad(
                    cert["round_id"],
                    cert["client_id"],
                    cert["model_hash"],
                    cert["key_context_id"]
                )

                list_of_ciphertexts.append({
                    "nonce": nonce,
                    "ciphertext": ciphertext,
                    "associated_data": aad
                })
                num_examples_list.append(fit_res.num_examples)

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
                    aggregated_weights = server_aggregate(list_of_ciphertexts, round_key, num_examples_list)
                except Exception as e:
                    print(f"Decryption / Aggregation failed: {e}")

            if aggregated_weights is None:
                # Log distinct event for expired/failed aggregation round
                write_audit_log(self.AUDIT_LOG_PATH, {
                    "event": "round_expired_no_aggregation",
                    "round_id": server_round,
                    "reason": "no_valid_updates_or_decryption_failed",
                    "timestamp": time.time()
                })
                return None, {}

            # Convert and return parameters
            params = fl.common.ndarrays_to_parameters(aggregated_weights)
            self.latest_ndarrays = aggregated_weights

            # Log distinct event for successful round close
            write_audit_log(self.AUDIT_LOG_PATH, {
                "event": "round_close",
                "round_id": server_round,
                "timestamp": time.time()
            })

            return params, {}

        finally:
            # 3. Wipe and destroy ephemeral round key + cached ciphertexts + replay state
            round_key = self.round_keys.get(self.current_key_context_id)
            if round_key is not None:
                destroy_round_key(round_key)
                self.round_keys.pop(self.current_key_context_id, None)

            self.cached_ciphertexts.pop(server_round, None)
            self.seen_updates.pop(server_round, None)
            list_of_ciphertexts.clear()

            # Separate timestamp for key_destroyed event
            write_audit_log(self.AUDIT_LOG_PATH, {
                "event": "key_destroyed",
                "round_id": server_round,
                "timestamp": time.time()
            })

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
    # 1. Reset skipped samples log and audit log
    log_path = "skipped_samples.log"
    if os.path.exists(log_path):
        os.remove(log_path)
    audit_log_path = "audit_log.jsonl"
    if os.path.exists(audit_log_path):
        os.remove(audit_log_path)

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

    local_epochs = 1
    window_seconds = (local_epochs * 700) + 1200

    strategy = TemporalCheckpointingSecAgg(
        mu=mu,
        C=C,
        sigma=sigma,
        secret_key=SECRET_KEY,
        window_seconds=window_seconds,
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
        client_resources["num_gpus"] = 0.33

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
    print("=== Running E7 Temporal Security Verification Tests ===")
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

    # --- Unit Tests A-D: Deterministic Model Hashing ---
    print("Running Hash Test A: Deterministic repeated hashing...")
    st1 = {"layer1.weight": torch.ones((5, 5), dtype=torch.float32)}
    h1 = compute_model_hash(st1)
    h2 = compute_model_hash(st1)
    assert h1 == h2, "Hash Test A failed: Repeated hashing was not deterministic"
    print("Hash Test A passed.")

    print("Running Hash Test B: Different tensor values => different hash...")
    st2 = {"layer1.weight": torch.zeros((5, 5), dtype=torch.float32)}
    h3 = compute_model_hash(st2)
    assert h1 != h3, "Hash Test B failed: Different tensor values produced same hash"
    print("Hash Test B passed.")

    print("Running Hash Test C: Different dtype => different hash...")
    st3 = {"layer1.weight": torch.ones((5, 5), dtype=torch.float64)}
    h4 = compute_model_hash(st3)
    assert h1 != h4, "Hash Test C failed: Different dtype produced same hash"
    print("Hash Test C passed.")

    print("Running Hash Test D: Different shape => different hash...")
    st4 = {"layer1.weight": torch.ones((5, 1), dtype=torch.float32)}
    h5 = compute_model_hash(st4)
    assert h1 != h5, "Hash Test D failed: Different shape produced same hash"
    print("Hash Test D passed.")

    # --- Setup test strategy and certificate ---
    round_id = 1
    key_context_id = str(uuid.uuid4())
    expiry_timestamp = time.time() + 10
    participants = ["client0", "client1", "client2"]
    model_hash = h1

    strategy = TemporalCheckpointingSecAgg(
        mu=0.001, C=2.0, sigma=1.5, secret_key=SECRET_KEY_TEST, window_seconds=10
    )
    strategy.current_key_context_id = key_context_id
    strategy.current_Tr = expiry_timestamp
    strategy.current_model_hash = model_hash
    strategy.AUDIT_LOG_PATH = AUDIT_LOG_PATH

    key = generate_round_key()
    strategy.round_keys[key_context_id] = key
    dummy_weights = [np.ones(10, dtype=np.float32)]

    client_id = "client0"
    aad = compute_aad(round_id, client_id, model_hash, key_context_id)
    ct = client_encrypt(dummy_weights, key, associated_data=aad)
    update_hash = hashlib.sha256(ct["nonce"] + ct["ciphertext"]).hexdigest()

    cert = create_certificate(
        round_id=round_id,
        model_hash=model_hash,
        participants=participants,
        key_context_id=key_context_id,
        expiry_timestamp=expiry_timestamp
    )
    cert["client_id"] = client_id
    cert["update_hash"] = update_hash
    signature = sign_certificate(cert, SECRET_KEY_TEST)

    # --- Tests E & F: Certificate Schema Fields ---
    print("Running Test E & F: Certificate contains client_id and update_hash...")
    assert cert.get("client_id") == client_id, "Test E failed: Missing client_id"
    assert cert.get("update_hash") == update_hash, "Test F failed: Missing update_hash"
    print("Test E & F passed.")

    class DummyClientProxy:
        def __init__(self, cid):
            self.cid = cid

    class DummyFitRes:
        def __init__(self, metrics, num_examples=100):
            self.metrics = metrics
            self.num_examples = num_examples

    fit_res_metrics = {
        "hospital_id": 0,
        "nonce_hex": ct["nonce"].hex(),
        "ciphertext_hex": ct["ciphertext"].hex(),
        "certificate": json.dumps(cert),
        "signature": signature,
        "key_context_id": key_context_id
    }
    client_proxy = DummyClientProxy("client0")
    fit_res = DummyFitRes(fit_res_metrics)

    # --- Test 1 / Test G: Valid submission & signature verification ---
    print("Running Test 1 (G): Timely submission & signature verification...")
    is_valid, reason = strategy.validate_update(fit_res, client_proxy=client_proxy, current_time=expiry_timestamp - 1.0)
    assert is_valid, f"Test 1 failed: update should be accepted, but got: {reason}"
    print("Test 1 passed: Timely submission accepted.")

    # --- Test G: Certificate signature rejects modification ---
    print("Running Test G: Certificate signature rejects modification...")
    bad_sig_metrics = fit_res_metrics.copy()
    bad_sig_metrics["signature"] = "0" * 64
    is_valid, reason = strategy.validate_update(DummyFitRes(bad_sig_metrics), client_proxy=client_proxy, current_time=expiry_timestamp - 1.0)
    assert not is_valid and reason == "invalid_signature", f"Test G failed: expected invalid_signature, got {reason}"
    print("Test G passed: Invalid signature rejected.")

    # --- Test 2 / Test H: Expired submission ---
    print("Running Test 2 (H): Submit update at Tr + 1s...")
    is_valid, reason = strategy.validate_update(fit_res, client_proxy=client_proxy, current_time=expiry_timestamp + 1.0)
    assert not is_valid and reason == "expired", f"Test 2 failed: expected 'expired', got {reason}"
    print("Test 2 passed: Expired submission rejected.")

    # --- Test I: Wrong model hash rejected ---
    print("Running Test I: Wrong model hash rejected...")
    wrong_mh_cert = cert.copy()
    wrong_mh_cert["model_hash"] = "wrong_model_hash_sha256"
    wrong_mh_sig = sign_certificate(wrong_mh_cert, SECRET_KEY_TEST)
    wrong_mh_metrics = fit_res_metrics.copy()
    wrong_mh_metrics["certificate"] = json.dumps(wrong_mh_cert)
    wrong_mh_metrics["signature"] = wrong_mh_sig
    is_valid, reason = strategy.validate_update(DummyFitRes(wrong_mh_metrics), client_proxy=client_proxy, current_time=expiry_timestamp - 1.0)
    assert not is_valid and reason == "model_hash_mismatch", f"Test I failed: expected model_hash_mismatch, got {reason}"
    print("Test I passed: Wrong model hash rejected.")

    # --- Test J: Wrong client ID rejected ---
    # --- Test J: Mismatched logical client identity rejected ---
    print("Running Test J: Mismatched client ID rejected...")
    wrong_client_metrics = fit_res_metrics.copy()
    wrong_client_cert = cert.copy()
    wrong_client_cert["client_id"] = "client1"
    wrong_client_metrics["certificate"] = json.dumps(wrong_client_cert)
    wrong_client_metrics["hospital_id"] = 0
    wrong_client_metrics["signature"] = sign_certificate(
        wrong_client_cert, SECRET_KEY_TEST
    )
    is_valid, reason = strategy.validate_update(
        DummyFitRes(wrong_client_metrics),
        client_proxy=client_proxy,
        current_time=expiry_timestamp - 1.0
    )
    assert not is_valid and reason == "wrong_client_id", \
        f"Test J failed: expected wrong_client_id, got {reason}"
    print("Test J passed: Mismatched logical client ID rejected.")

    # --- Test K: Duplicate update (replay) rejected ---
    print("Running Test K: Duplicate update rejected...")
    strategy.seen_updates[round_id] = set()
    is_valid1, reason1 = strategy.validate_update(fit_res, client_proxy=client_proxy, current_time=expiry_timestamp - 1.0)
    assert is_valid1, f"First submission should be accepted: {reason1}"
    is_valid2, reason2 = strategy.validate_update(fit_res, client_proxy=client_proxy, current_time=expiry_timestamp - 1.0)
    assert not is_valid2 and reason2 == "replay_detected", f"Test K failed: expected replay_detected, got {reason2}"
    print("Test K passed: Replay rejected.")

    # --- Test L & M: Modified ciphertext & AAD mismatch rejection during aggregation ---
    print("Running Test L & M: Modified ciphertext and AAD mismatch decryption failure...")
    bad_aad = compute_aad(round_id, client_id, "wrong_model_hash", key_context_id)
    ct_bad_aad = {"nonce": ct["nonce"], "ciphertext": ct["ciphertext"], "associated_data": bad_aad}
    try:
        decrypt_update(ct_bad_aad, key)
        assert False, "Test M failed: Decryption should fail on AAD mismatch"
    except InvalidTag:
        print("Test L & M passed: AAD mismatch raised InvalidTag during decryption.")

    # --- Test 3: Key context mismatch ---
    print("Running Test 3: Submit update with wrong key_context_id...")
    wrong_ctx_cert = cert.copy()
    wrong_ctx_cert["key_context_id"] = str(uuid.uuid4())
    wrong_ctx_sig = sign_certificate(wrong_ctx_cert, SECRET_KEY_TEST)
    wrong_ctx_metrics = fit_res_metrics.copy()
    wrong_ctx_metrics["key_context_id"] = wrong_ctx_cert["key_context_id"]
    wrong_ctx_metrics["certificate"] = json.dumps(wrong_ctx_cert)
    wrong_ctx_metrics["signature"] = wrong_ctx_sig
    is_valid, reason = strategy.validate_update(DummyFitRes(wrong_ctx_metrics), client_proxy=client_proxy, current_time=expiry_timestamp - 1.0)
    assert not is_valid and reason == "mismatch", f"Test 3 failed: expected 'mismatch', got {reason}"
    print("Test 3 passed: Key context mismatch rejected.")

    # --- Test 4: Post-expiry key destruction ---
    print("Running Test 4: Post-expiry decryption attempt must fail...")
    key_copy = bytearray(key)
    destroy_round_key(key_copy)
    try:
        decrypt_update(ct, key_copy)
        assert False, "Test 4 failed: Decryption succeeded with destroyed key!"
    except InvalidTag:
        print("Test 4 passed: Decryption with destroyed key raised InvalidTag.")

    # --- Test N & Test 5: Full strategy execution & replay state cleanup & audit logs ---
    print("Running Test N & Test 5: Full round aggregation and cleanup...")
    class DummyClientManager:
        def sample(self, num_clients, min_num_clients=None):
            return [DummyClientProxy("client0"), DummyClientProxy("client1"), DummyClientProxy("client2")]
        def num_available(self):
            return 3

    test_model = ResUNetPlusPlus()
    fix_model_for_opacus(test_model)
    test_params = fl.common.ndarrays_to_parameters(get_parameters(test_model))

    # Reset strategy
    fresh_strategy = TemporalCheckpointingSecAgg(
        mu=0.001, C=2.0, sigma=1.5, secret_key=SECRET_KEY_TEST, window_seconds=10
    )
    fresh_strategy.AUDIT_LOG_PATH = AUDIT_LOG_PATH

    fit_configs = fresh_strategy.configure_fit(server_round=1, parameters=test_params, client_manager=DummyClientManager())
    client_config = fit_configs[0][1].config

    # Simulate client fitting using TemporalHospitalClient logic
    client_cert_str = client_config["certificate"]
    c_cert = json.loads(client_cert_str)
    c_cert["client_id"] = "client0"
    c_aad = compute_aad(c_cert["round_id"], c_cert["client_id"], c_cert["model_hash"], c_cert["key_context_id"])
    c_key = bytearray(bytes.fromhex(client_config["round_key_hex"]))
    c_ct = client_encrypt(dummy_weights, c_key, associated_data=c_aad)
    c_cert["update_hash"] = hashlib.sha256(c_ct["nonce"] + c_ct["ciphertext"]).hexdigest()
    c_sig = sign_certificate(c_cert, SECRET_KEY_TEST)

    fresh_fit_res_metrics = {
        "hospital_id": 0,
        "nonce_hex": c_ct["nonce"].hex(),
        "ciphertext_hex": c_ct["ciphertext"].hex(),
        "certificate": json.dumps(c_cert),
        "signature": c_sig,
        "key_context_id": c_cert["key_context_id"]
    }
    fit_results = [(DummyClientProxy("client0"), DummyFitRes(fresh_fit_res_metrics))]

    fresh_strategy.aggregate_fit(server_round=1, results=fit_results, failures=[])

    # Check that replay state and cached ciphertexts were cleaned after round
    assert 1 not in fresh_strategy.seen_updates, "Test N failed: replay state was not cleaned after round"
    assert 1 not in fresh_strategy.cached_ciphertexts, "Test N failed: cached ciphertexts were not cleaned after round"
    print("Test N passed: Replay state and cached ciphertexts cleaned after round.")

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

    print("All E7 security verification tests passed successfully!\n")


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
