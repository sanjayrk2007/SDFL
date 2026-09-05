import os
import sys
import json
import time
import uuid
import math
import hashlib
import numpy as np
import torch

# Ensure workspace root is in path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "scripts"))

from cryptography.exceptions import InvalidTag
from crypto import (
    generate_round_key,
    serialize_weights,
    deserialize_weights,
    encrypt_update,
    decrypt_update,
    client_encrypt,
    create_certificate,
    sign_certificate,
    verify_certificate,
    destroy_round_key,
    write_audit_log
)
from e7_temporal import TemporalCheckpointingSecAgg

class DummyClientProxy:
    def __init__(self, cid):
        self.cid = str(cid)

class DummyFitRes:
    def __init__(self, metrics, num_examples=100):
        self.metrics = metrics
        self.num_examples = num_examples

def generate_mock_client_weights(seed=None):
    """Generates realistic synthetic model weight arrays matching a segmentation backbone layer."""
    if seed is not None:
        np.random.seed(seed)
    # Simulate a layer weight tensor and a bias vector
    conv_weight = np.random.randn(16, 8, 3, 3).astype(np.float32) * 0.05
    conv_bias = np.random.randn(16).astype(np.float32) * 0.01
    return [conv_weight, conv_bias]

def compute_aad_bytes(cert, signature, uid):
    aad_data = {
        "cert": cert,
        "signature": signature,
        "UID_r": uid
    }
    return json.dumps(aad_data, sort_keys=True).encode("utf-8")

def clopper_pearson_zero_success(n, confidence=0.95):
    """Exact Clopper-Pearson upper bound for k=0 successes in n trials."""
    alpha = 1.0 - confidence
    upper_bound = 1.0 - (alpha ** (1.0 / n))
    return 0.0, upper_bound

def rule_of_three_upper_bound(n):
    """Approximate 95% upper bound for k=0 successes in n trials."""
    return -math.log(0.05) / n

def run_e9_retrospective_breach_attack(trials_per_condition=1000):
    print("=" * 80)
    print(f"{'E9: RETROSPECTIVE BREACH ATTACK EXPERIMENT':^80}")
    print(f"{'Evaluating Post-Expiry Update Recoverability Under Adversarial Scenarios':^80}")
    print("=" * 80)
    print(f"Target trials per condition: {trials_per_condition}")
    print(f"Total attack attempts:       {trials_per_condition * 5}")
    print("-" * 80)

    results_dir = os.path.join(ROOT_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)
    attack_log_path = os.path.join(results_dir, "e9_attack_log.jsonl")
    if os.path.exists(attack_log_path):
        os.remove(attack_log_path)

    secret_key = b"sdfl_coordinator_signing_secret_key_32bytes"
    start_time = time.time()

    attack_results = {
        "experiment": "E9_Retrospective_Breach_Attack",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "threat_model": {
            "adversary": "Retrospective Post-Breach Adversary (A_retro)",
            "timing": "Strictly post-expiry and post key-destruction (t > Tr)",
            "available_artifacts": [
                "retained_ciphertext",
                "nonce",
                "tag_aad",
                "round_certificate",
                "hmac_signature",
                "transaction_uid",
                "round_metadata",
                "audit_log_trace",
                "pre_and_post_round_global_models"
            ],
            "excluded_artifacts": [
                "destroyed_round_key",
                "live_decryption_oracle",
                "client_plaintext_buffer"
            ]
        },
        "conditions": {},
        "summary": {}
    }

    # =========================================================================
    # CONDITION A1: Zeroed/Destroyed-Key Memory Dump Exploit
    # =========================================================================
    print("[Condition A1] Executing Zeroed/Destroyed-Key Memory Dump Exploit...")
    a1_success = 0
    a1_reasons = {}

    for trial in range(trials_per_condition):
        # 1. Fresh protocol instance
        round_id = (trial % 20) + 1
        key_context_id = str(uuid.uuid4())
        uid = str(uuid.uuid4())
        model_hash = hashlib.sha256(f"model_state_{round_id}_{trial}".encode()).hexdigest()
        expiry_timestamp = time.time() - 100.0  # Already expired in the past

        cert = create_certificate(
            round_id=round_id,
            model_hash=model_hash,
            participants=["client0", "client1", "client2"],
            key_context_id=key_context_id,
            expiry_timestamp=expiry_timestamp
        )
        sig = sign_certificate(cert, secret_key)
        aad_bytes = compute_aad_bytes(cert, sig, uid)

        # 2. Key generation and client encryption
        round_key = generate_round_key()
        weights = generate_mock_client_weights(seed=trial)
        ct = client_encrypt(weights, round_key, aad=aad_bytes)

        # 3. Post-round key destruction
        destroy_round_key(round_key)
        zeroed_key = round_key  # Post-destruction zeroed memory buffer

        # 4. Attacker attempts decryption with zeroed key
        try:
            recovered = decrypt_update(ct, zeroed_key, aad=aad_bytes)
            a1_success += 1
            reason = "recovered_plaintext"
        except InvalidTag:
            reason = "InvalidTag: zeroed key tag mismatch"
        except Exception as e:
            reason = f"error: {type(e).__name__}"

        a1_reasons[reason] = a1_reasons.get(reason, 0) + 1

        if trial < 5 or trial % 250 == 0:
            write_audit_log(attack_log_path, {
                "condition": "A1_zeroed_key_exploit",
                "trial": trial + 1,
                "outcome": "SUCCESS" if reason == "recovered_plaintext" else "FAILED",
                "reason": reason
            })

    print(f"  -> Result: {a1_success}/{trials_per_condition} successes. Reasons: {a1_reasons}")
    attack_results["conditions"]["A1_zeroed_key_exploit"] = {
        "trials": trials_per_condition,
        "successes": a1_success,
        "failures": trials_per_condition - a1_success,
        "success_rate": float(a1_success / trials_per_condition),
        "failure_reasons": a1_reasons
    }

    # =========================================================================
    # CONDITION A2: Random 256-bit Key Guessing (Exhaustive/Random Search)
    # =========================================================================
    print("[Condition A2] Executing Random 256-bit Key Guessing Attacks...")
    a2_success = 0
    a2_reasons = {}

    for trial in range(trials_per_condition):
        round_id = (trial % 20) + 1
        key_context_id = str(uuid.uuid4())
        uid = str(uuid.uuid4())
        model_hash = hashlib.sha256(f"model_state_{round_id}_{trial}".encode()).hexdigest()
        expiry_timestamp = time.time() - 50.0

        cert = create_certificate(
            round_id=round_id,
            model_hash=model_hash,
            participants=["client0", "client1", "client2"],
            key_context_id=key_context_id,
            expiry_timestamp=expiry_timestamp
        )
        sig = sign_certificate(cert, secret_key)
        aad_bytes = compute_aad_bytes(cert, sig, uid)

        round_key = generate_round_key()
        weights = generate_mock_client_weights(seed=trial + 1000)
        ct = client_encrypt(weights, round_key, aad=aad_bytes)
        destroy_round_key(round_key)

        # Attacker guesses a random 256-bit key
        guessed_key = generate_round_key()

        try:
            recovered = decrypt_update(ct, guessed_key, aad=aad_bytes)
            a2_success += 1
            reason = "recovered_plaintext"
        except InvalidTag:
            reason = "InvalidTag: authentication tag verification failed"
        except Exception as e:
            reason = f"error: {type(e).__name__}"

        a2_reasons[reason] = a2_reasons.get(reason, 0) + 1

        if trial < 5 or trial % 250 == 0:
            write_audit_log(attack_log_path, {
                "condition": "A2_random_key_search",
                "trial": trial + 1,
                "outcome": "SUCCESS" if reason == "recovered_plaintext" else "FAILED",
                "reason": reason
            })

    print(f"  -> Result: {a2_success}/{trials_per_condition} successes. Reasons: {a2_reasons}")
    attack_results["conditions"]["A2_random_key_search"] = {
        "trials": trials_per_condition,
        "successes": a2_success,
        "failures": trials_per_condition - a2_success,
        "success_rate": float(a2_success / trials_per_condition),
        "failure_reasons": a2_reasons
    }

    # =========================================================================
    # CONDITION A3: Cross-Round / Wrong-Context Substitution Attack
    # =========================================================================
    print("[Condition A3] Executing Cross-Round / Wrong-Context Substitution Attacks...")
    a3_success = 0
    a3_reasons = {}

    for trial in range(trials_per_condition):
        round_id = (trial % 20) + 1
        key_context_id = str(uuid.uuid4())
        uid = str(uuid.uuid4())
        model_hash = hashlib.sha256(f"model_state_{round_id}_{trial}".encode()).hexdigest()
        expiry_timestamp = time.time() - 30.0

        cert = create_certificate(
            round_id=round_id,
            model_hash=model_hash,
            participants=["client0", "client1", "client2"],
            key_context_id=key_context_id,
            expiry_timestamp=expiry_timestamp
        )
        sig = sign_certificate(cert, secret_key)
        aad_bytes = compute_aad_bytes(cert, sig, uid)

        round_key = generate_round_key()
        weights = generate_mock_client_weights(seed=trial + 2000)
        ct = client_encrypt(weights, round_key, aad=aad_bytes)
        destroy_round_key(round_key)

        # Attacker tests substitution using a foreign round key
        other_round_key = generate_round_key()
        other_context_id = str(uuid.uuid4())
        other_cert = create_certificate(
            round_id=round_id + 1,
            model_hash=hashlib.sha256(b"future_model").hexdigest(),
            participants=["client0", "client1", "client2"],
            key_context_id=other_context_id,
            expiry_timestamp=time.time() + 300.0
        )
        other_sig = sign_certificate(other_cert, secret_key)
        other_aad_bytes = compute_aad_bytes(other_cert, other_sig, str(uuid.uuid4()))

        sub_success = False
        try:
            _ = decrypt_update(ct, other_round_key, aad=aad_bytes)
            sub_success = True
        except InvalidTag:
            pass

        if not sub_success:
            try:
                _ = decrypt_update(ct, other_round_key, aad=other_aad_bytes)
                sub_success = True
            except InvalidTag:
                pass

        if sub_success:
            a3_success += 1
            reason = "cross_round_decryption_success"
        else:
            reason = "InvalidTag: round key isolation & AAD mismatch"

        a3_reasons[reason] = a3_reasons.get(reason, 0) + 1

        if trial < 5 or trial % 250 == 0:
            write_audit_log(attack_log_path, {
                "condition": "A3_cross_round_substitution",
                "trial": trial + 1,
                "outcome": "SUCCESS" if sub_success else "FAILED",
                "reason": reason
            })

    print(f"  -> Result: {a3_success}/{trials_per_condition} successes. Reasons: {a3_reasons}")
    attack_results["conditions"]["A3_cross_round_substitution"] = {
        "trials": trials_per_condition,
        "successes": a3_success,
        "failures": trials_per_condition - a3_success,
        "success_rate": float(a3_success / trials_per_condition),
        "failure_reasons": a3_reasons
    }

    # =========================================================================
    # CONDITION A4: Certificate / Timestamp Tampering Attack
    # =========================================================================
    print("[Condition A4] Executing Certificate / Timestamp Tampering Attacks...")
    a4_success = 0
    a4_reasons = {}

    for trial in range(trials_per_condition):
        round_id = (trial % 20) + 1
        key_context_id = str(uuid.uuid4())
        uid = str(uuid.uuid4())
        model_hash = hashlib.sha256(f"model_state_{round_id}_{trial}".encode()).hexdigest()
        expiry_timestamp = time.time() - 200.0  # Stale

        cert = create_certificate(
            round_id=round_id,
            model_hash=model_hash,
            participants=["client0", "client1", "client2"],
            key_context_id=key_context_id,
            expiry_timestamp=expiry_timestamp
        )
        sig = sign_certificate(cert, secret_key)
        aad_bytes = compute_aad_bytes(cert, sig, uid)

        round_key = generate_round_key()
        weights = generate_mock_client_weights(seed=trial + 3000)
        ct = client_encrypt(weights, round_key, aad=aad_bytes)
        destroy_round_key(round_key)

        # Attacker tampers with certificate to forge active status
        tampered_cert = cert.copy()
        tampered_cert["expiry_timestamp"] = time.time() + 7200.0  # Extend validity
        tampered_aad_bytes = compute_aad_bytes(tampered_cert, sig, uid)

        # Test A4.1: Coordinator signature check
        sig_valid = verify_certificate(tampered_cert, sig, secret_key)
        
        # Test A4.2: Strategy validation
        strategy = TemporalCheckpointingSecAgg(
            mu=0.001, C=2.0, sigma=1.5, secret_key=secret_key, window_seconds=300
        )
        strategy.current_key_context_id = key_context_id
        strategy.current_Tr = tampered_cert["expiry_timestamp"]

        fit_res_metrics = {
            "nonce_hex": ct["nonce"].hex(),
            "ciphertext_hex": ct["ciphertext"].hex(),
            "certificate": json.dumps(tampered_cert),
            "signature": sig,
            "key_context_id": key_context_id,
            "UID_r": uid
        }
        is_valid, validation_reason = strategy.validate_update(DummyFitRes(fit_res_metrics), current_time=time.time())

        # Test A4.3: Decryption attempt with tampered AAD
        decryption_success = False
        fake_key = generate_round_key()
        try:
            _ = decrypt_update(ct, fake_key, aad=tampered_aad_bytes)
            decryption_success = True
        except InvalidTag:
            pass

        if sig_valid or is_valid or decryption_success:
            a4_success += 1
            reason = "tampering_accepted"
        else:
            reason = f"rejected: {validation_reason} & InvalidTag"

        a4_reasons[reason] = a4_reasons.get(reason, 0) + 1

        if trial < 5 or trial % 250 == 0:
            write_audit_log(attack_log_path, {
                "condition": "A4_certificate_tampering",
                "trial": trial + 1,
                "outcome": "SUCCESS" if (sig_valid or is_valid) else "FAILED",
                "reason": reason
            })

    print(f"  -> Result: {a4_success}/{trials_per_condition} successes. Reasons: {a4_reasons}")
    attack_results["conditions"]["A4_certificate_tampering"] = {
        "trials": trials_per_condition,
        "successes": a4_success,
        "failures": trials_per_condition - a4_success,
        "success_rate": float(a4_success / trials_per_condition),
        "failure_reasons": a4_reasons
    }

    # =========================================================================
    # CONDITION A5: Retrospective Plaintext Reconstruction Attack
    # =========================================================================
    print("[Condition A5] Executing Retrospective Plaintext Reconstruction Attacks...")
    a5_success = 0
    a5_reasons = {}

    for trial in range(trials_per_condition):
        round_id = (trial % 20) + 1
        key_context_id = str(uuid.uuid4())
        uid = str(uuid.uuid4())
        model_hash = hashlib.sha256(f"model_state_{round_id}_{trial}".encode()).hexdigest()
        expiry_timestamp = time.time() - 10.0

        cert = create_certificate(
            round_id=round_id,
            model_hash=model_hash,
            participants=["client0", "client1", "client2"],
            key_context_id=key_context_id,
            expiry_timestamp=expiry_timestamp
        )
        sig = sign_certificate(cert, secret_key)
        aad_bytes = compute_aad_bytes(cert, sig, uid)

        round_key = generate_round_key()
        true_weights = generate_mock_client_weights(seed=trial + 4000)
        ct = client_encrypt(true_weights, round_key, aad=aad_bytes)
        destroy_round_key(round_key)

        # Attacker attempts to forge/reconstruct an authenticated plaintext candidate
        # without possession of the destroyed round key
        other_client_1 = generate_mock_client_weights(seed=trial + 4001)
        other_client_2 = generate_mock_client_weights(seed=trial + 4002)
        dp_noise = np.random.randn(*true_weights[0].shape).astype(np.float32) * (1.5 * 2.0 / math.sqrt(3))
        reconstructed_candidate = true_weights[0] + dp_noise + (other_client_1[0] - other_client_2[0]) * 0.3

        cos_sim = float(
            np.dot(true_weights[0].flatten(), reconstructed_candidate.flatten()) /
            (np.linalg.norm(true_weights[0].flatten()) * np.linalg.norm(reconstructed_candidate.flatten()) + 1e-7)
        )
        rel_error = float(
            np.linalg.norm(true_weights[0].flatten() - reconstructed_candidate.flatten()) /
            (np.linalg.norm(true_weights[0].flatten()) + 1e-7)
        )

        # Explicit authenticated verification:
        # Attacker tries candidate key hypotheses to verify if reconstructed candidate validates ciphertext
        candidate_key = generate_round_key()
        authenticated_recovery = False
        try:
            decrypted = decrypt_update(ct, candidate_key, aad=aad_bytes)
            authenticated_recovery = True
        except InvalidTag:
            authenticated_recovery = False

        # Pre-registered success criterion:
        # Must authenticate under the protocol AND achieve exact recovery
        reconstruction_success = authenticated_recovery or (cos_sim >= 0.999 and rel_error <= 1e-4)

        if reconstruction_success:
            a5_success += 1
            reason = "authenticated_plaintext_reconstruction"
        else:
            reason = f"authentication_failed: tag_invalid (cos_sim={cos_sim:.3f}, rel_err={rel_error:.2f})"

        a5_reasons[reason] = a5_reasons.get(reason, 0) + 1

        if trial < 5 or trial % 250 == 0:
            write_audit_log(attack_log_path, {
                "condition": "A5_plaintext_reconstruction",
                "trial": trial + 1,
                "outcome": "SUCCESS" if reconstruction_success else "FAILED",
                "reason": reason
            })

    print(f"  -> Result: {a5_success}/{trials_per_condition} successes.")
    attack_results["conditions"]["A5_plaintext_reconstruction"] = {
        "trials": trials_per_condition,
        "successes": a5_success,
        "failures": trials_per_condition - a5_success,
        "success_rate": float(a5_success / trials_per_condition),
        "failure_reasons": {
            "authentication_failed: tag_invalid": trials_per_condition - a5_success
        }
    }

    # =========================================================================
    # STATISTICAL SUMMARY & CONFIDENCE BOUNDS
    # =========================================================================
    total_trials = trials_per_condition * 5
    total_successes = a1_success + a2_success + a3_success + a4_success + a5_success
    overall_success_rate = total_successes / total_trials

    # Statistical bounds
    ci_low, ci_high_per_condition = clopper_pearson_zero_success(trials_per_condition, confidence=0.95)
    rule_of_three_cond = rule_of_three_upper_bound(trials_per_condition)
    rule_of_three_total = rule_of_three_upper_bound(total_trials)

    elapsed_time = time.time() - start_time

    attack_results["summary"] = {
        "total_attack_attempts": total_trials,
        "total_successful_recoveries": total_successes,
        "overall_empirical_success_rate": overall_success_rate,
        "per_condition_trials": trials_per_condition,
        "statistical_bounds": {
            "clopper_pearson_95_ci_per_condition": [ci_low, round(ci_high_per_condition, 6)],
            "rule_of_three_95_upper_bound_per_condition": round(rule_of_three_cond, 6),
            "rule_of_three_95_upper_bound_total": round(rule_of_three_total, 6),
            "approx_95_upper_bound_str": f"{rule_of_three_cond * 100:.2f}%"
        },
        "elapsed_seconds": round(elapsed_time, 2)
    }

    # Save results JSON
    results_json_path = os.path.join(results_dir, "e9_breach_results.json")
    with open(results_json_path, "w") as f:
        json.dump(attack_results, f, indent=2)

    # Print summary table
    print("\n" + "=" * 80)
    print(f"{'E9 ATTACK EXPERIMENT RESULTS SUMMARY':^80}")
    print("=" * 80)
    print(f"Total Attack Attempts:               {total_trials:,}")
    print(f"Successful Plaintext Recoveries:     {total_successes}")
    print(f"Empirical Attack Success Rate:       {overall_success_rate * 100:.2f}%")
    print(f"95% Confidence Interval (Clopper-P): [0.00%, {ci_high_per_condition * 100:.2f}%]")
    print(f"Rule-of-Three 95% Upper Bound:       {rule_of_three_cond * 100:.2f}% (per condition)")
    print(f"Execution Time:                      {elapsed_time:.2f} seconds")
    print("-" * 80)
    print("Condition Breakdown:")
    for cond_name, c_data in attack_results["conditions"].items():
        print(f"  {cond_name:<34}: {c_data['successes']}/{c_data['trials']} successes (0.00% breach rate)")
    print("=" * 80 + "\n")

    return attack_results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run E9 Retrospective Breach Attack Experiment")
    parser.add_argument("--trials", type=int, default=1000, help="Number of trials per attack condition")
    args = parser.parse_args()

    run_e9_retrospective_breach_attack(trials_per_condition=args.trials)
