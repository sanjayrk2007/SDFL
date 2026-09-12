#!/usr/bin/env python3
"""
SDFL Security Attack Evaluation Harness (Experiment E9)
======================================================
Tests the 14 security conditions of Self-Destructing Federated Learning (SDFL):
 1. Timely valid update
 2. Expired update
 3. Replayed update
 4. Tampered certificate
 5. Wrong key
 6. Wrong key_context_id
 7. Wrong round_id
 8. Wrong model hash
 9. Cross-round substitution
10. Post-destruction decryption
11. Duplicate update ID
12. Modified ciphertext
13. Modified nonce
14. Modified AAD

For each condition, runs randomized attempts (>= 1000 total across seeds),
records exact validation rules / rejection reasons, timing, and produces
machine-readable JSON + formatted summary table.
"""

import os
import sys
import json
import time
import uuid
import random
import hashlib
import argparse
import numpy as np
import torch
from typing import Dict, Any, List, Tuple
from cryptography.exceptions import InvalidTag

# Ensure project root directory is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from crypto import (
    generate_round_key,
    client_encrypt,
    decrypt_update,
    destroy_round_key,
    create_certificate,
    sign_certificate,
    verify_certificate,
)
from e7_temporal import (
    TemporalCheckpointingSecAgg,
    compute_aad,
    compute_model_hash,
    SECRET_KEY,
)


class DummyClientProxy:
    def __init__(self, cid="client0"):
        self.cid = str(cid)


class DummyFitRes:
    def __init__(self, metrics, num_examples=100):
        self.metrics = metrics
        self.num_examples = num_examples


def create_baseline_update(
    server_round: int = 1,
    client_id: str = "client0",
    secret_key: bytes = SECRET_KEY,
    window_seconds: float = 300.0,

) -> Dict[str, Any]:
    """
    Creates a fresh, legitimate SDFL model update and matching certificate.
    """
    key_context_id = str(uuid.uuid4())
    now = time.time()
    expiry_timestamp = now + window_seconds
    participants = ["client0", "client1", "client2"]

    # Random dummy model weights for serialization test
    weights = [
        np.random.randn(8, 8).astype(np.float32),
        np.random.randn(8).astype(np.float32),
    ]

    # Generate model hash from tensor dictionary
    st = {
        "layer1.weight": torch.from_numpy(weights[0]),
        "layer1.bias": torch.from_numpy(weights[1]),
    }
    model_hash = compute_model_hash(st)

    round_key = generate_round_key()

    aad = compute_aad(server_round, client_id, model_hash, key_context_id)
    ct = client_encrypt(weights, round_key, associated_data=aad)

    update_hash = hashlib.sha256(ct["nonce"] + ct["ciphertext"]).hexdigest()

    cert = create_certificate(
        round_id=server_round,
        model_hash=model_hash,
        participants=participants,
        key_context_id=key_context_id,
        expiry_timestamp=expiry_timestamp,
    )
    cert["client_id"] = client_id
    cert["update_hash"] = update_hash

    signature = sign_certificate(cert, secret_key)

    metrics = {
        "nonce_hex": ct["nonce"].hex(),
        "ciphertext_hex": ct["ciphertext"].hex(),
        "certificate": json.dumps(cert),
        "signature": signature,
        "key_context_id": key_context_id,
        "client_id": client_id,
    }

    return {
        "server_round": server_round,
        "client_id": client_id,
        "key_context_id": key_context_id,
        "expiry_timestamp": expiry_timestamp,
        "participants": participants,
        "weights": weights,
        "model_hash": model_hash,
        "round_key": round_key,
        "aad": aad,
        "ct": ct,
        "update_hash": update_hash,
        "cert": cert,
        "signature": signature,
        "metrics": metrics,
    }


def evaluate_update_pipeline(
    strategy: TemporalCheckpointingSecAgg,
    fit_res: DummyFitRes,
    client_proxy: DummyClientProxy,
    current_time: float,
    decryption_key: bytearray,
    expected_aad: bytes = None,

) -> Tuple[bool, str]:
    """
    Evaluates a candidate update through the two-stage SDFL security pipeline:
    Stage 1: Strategy Certificate & Metadata Validator (validate_update)
    Stage 2: AEAD AES-GCM Decryption (decrypt_update)

    Returns:
        (is_accepted_and_decrypted: bool, exact_rejection_reason: str)
    """
    # Stage 1: Server strategy validation
    is_valid, reason = strategy.validate_update(
        fit_res, client_proxy=client_proxy, current_time=current_time
    )

    if not is_valid:
        return False, reason

    # Stage 2: AEAD Decryption verification
    try:
        ct_dict = {
            "nonce": bytes.fromhex(fit_res.metrics["nonce_hex"]),
            "ciphertext": bytes.fromhex(fit_res.metrics["ciphertext_hex"]),
        }

        # If aad is provided or derived from cert
        aad_to_use = expected_aad
        if aad_to_use is None:
            cert = json.loads(fit_res.metrics["certificate"])
            aad_to_use = compute_aad(
                cert["round_id"],
                cert.get("client_id", "client0"),
                cert.get("model_hash", ""),
                cert.get("key_context_id", ""),
            )

        _ = decrypt_update(ct_dict, decryption_key, associated_data=aad_to_use)
        return True, "accepted"
    except InvalidTag:
        return False, "decryption_failed_invalid_tag"
    except Exception as e:
        return False, f"decryption_failed_{type(e).__name__}"


def run_condition_tests(
    condition_id: int,
    condition_name: str,
    seeds: List[int],
    attempts_per_seed: int,

) -> Dict[str, Any]:
    """
    Executes randomized test attempts for a specific security condition across multiple seeds.
    """
    total_attempts = len(seeds) * attempts_per_seed
    accepted_count = 0
    rejected_count = 0
    reason_distribution: Dict[str, int] = {}

    start_time = time.time()

    for seed in seeds:
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)

        for attempt_idx in range(attempts_per_seed):
            # Setup strategy for this attempt
            secret_key = SECRET_KEY
            strategy = TemporalCheckpointingSecAgg(
                mu=0.001,
                C=2.0,
                sigma=1.5,
                secret_key=secret_key,
                window_seconds=300.0,
            )

            # Generate base update
            base = create_baseline_update(
                server_round=1, client_id="client0", secret_key=secret_key
            )

            # Configure strategy state
            strategy.current_key_context_id = base["key_context_id"]
            strategy.current_Tr = base["expiry_timestamp"]
            strategy.current_model_hash = base["model_hash"]
            strategy.round_keys[base["key_context_id"]] = base["round_key"]

            eval_time = base["expiry_timestamp"] - random.uniform(10.0, 100.0)
            client_proxy = DummyClientProxy("client0")

            target_fit_res = DummyFitRes(dict(base["metrics"]))
            target_key = base["round_key"]
            target_aad = base["aad"]
            target_eval_time = eval_time

            # Apply specific condition mutations
            if condition_id == 1:
                # 1. Timely valid update
                pass

            elif condition_id == 2:
                # 2. Expired update
                expired_delta = random.uniform(1.0, 500.0)
                target_eval_time = base["expiry_timestamp"] + expired_delta

            elif condition_id == 3:
                # 3. Replayed update
                # Pre-register update in seen_updates
                round_seen = strategy.seen_updates.setdefault(1, set())
                round_seen.add(("client0", base["update_hash"]))

            elif condition_id == 4:
                # 4. Tampered certificate
                field_to_tamper = random.choice([
                    "expiry_timestamp", "model_hash", "key_context_id",
                    "round_id", "client_id", "participants", "update_hash"
                ])
                cert = json.loads(target_fit_res.metrics["certificate"])
                if field_to_tamper == "expiry_timestamp":
                    cert["expiry_timestamp"] += random.uniform(10, 100)
                elif field_to_tamper == "model_hash":
                    cert["model_hash"] = hashlib.sha256(os.urandom(16)).hexdigest()
                elif field_to_tamper == "key_context_id":
                    cert["key_context_id"] = str(uuid.uuid4())
                elif field_to_tamper == "round_id":
                    cert["round_id"] += random.randint(1, 10)
                elif field_to_tamper == "client_id":
                    cert["client_id"] = "client_attacker"
                elif field_to_tamper == "participants":
                    cert["participants"] = ["client99"]
                elif field_to_tamper == "update_hash":
                    cert["update_hash"] = hashlib.sha256(os.urandom(16)).hexdigest()

                target_fit_res.metrics["certificate"] = json.dumps(cert)
                # Signature left unchanged (not re-signed for tampered cert)

            elif condition_id == 5:
                # 5. Wrong key
                # Encrypt with a different wrong key
                wrong_key = generate_round_key()
                ct_wrong = client_encrypt(base["weights"], wrong_key, associated_data=base["aad"])
                target_fit_res.metrics["nonce_hex"] = ct_wrong["nonce"].hex()
                target_fit_res.metrics["ciphertext_hex"] = ct_wrong["ciphertext"].hex()
                # Update hash & signature kept valid for metadata
                cert = json.loads(target_fit_res.metrics["certificate"])
                cert["update_hash"] = hashlib.sha256(ct_wrong["nonce"] + ct_wrong["ciphertext"]).hexdigest()
                target_fit_res.metrics["certificate"] = json.dumps(cert)
                target_fit_res.metrics["signature"] = sign_certificate(cert, secret_key)

            elif condition_id == 6:
                # 6. Wrong key_context_id
                wrong_context_id = str(uuid.uuid4())
                cert = json.loads(target_fit_res.metrics["certificate"])
                cert["key_context_id"] = wrong_context_id
                target_fit_res.metrics["key_context_id"] = wrong_context_id
                target_fit_res.metrics["certificate"] = json.dumps(cert)
                # Re-signed to isolate key_context_id rule
                target_fit_res.metrics["signature"] = sign_certificate(cert, secret_key)

            elif condition_id == 7:
                # 7. Wrong round_id
                wrong_round = base["server_round"] + random.choice([-5, -1, 1, 5, 10])
                cert = json.loads(target_fit_res.metrics["certificate"])
                cert["round_id"] = wrong_round

                variant = attempt_idx % 2
                if variant == 0:
                    # Unsigned round modification
                    target_fit_res.metrics["certificate"] = json.dumps(cert)
                else:
                    # Re-signed cert with wrong round_id
                    target_fit_res.metrics["certificate"] = json.dumps(cert)
                    target_fit_res.metrics["signature"] = sign_certificate(cert, secret_key)
                    # Recompute target_aad with wrong_round to test AES-GCM tag check if signature passes
                    target_aad = compute_aad(wrong_round, "client0", cert["model_hash"], cert["key_context_id"])

            elif condition_id == 8:
                # 8. Wrong model hash
                wrong_hash = hashlib.sha256(os.urandom(32)).hexdigest()
                cert = json.loads(target_fit_res.metrics["certificate"])
                cert["model_hash"] = wrong_hash
                target_fit_res.metrics["certificate"] = json.dumps(cert)

                variant = attempt_idx % 2
                if variant == 1:
                    # Re-signed to isolate model_hash_mismatch validator rule
                    target_fit_res.metrics["signature"] = sign_certificate(cert, secret_key)

            elif condition_id == 9:
                # 9. Cross-round substitution
                # Round 1 update presented to Round 2 strategy
                round2_context_id = str(uuid.uuid4())
                round2_key = generate_round_key()

                strategy.current_key_context_id = round2_context_id
                strategy.round_keys[round2_context_id] = round2_key
                # Old Round 1 key destroyed
                destroy_round_key(base["round_key"])

            elif condition_id == 10:
                # 10. Post-destruction decryption
                # Zero out key in memory
                key_to_destroy = bytearray(target_key)
                destroy_round_key(key_to_destroy)
                target_key = key_to_destroy

            elif condition_id == 11:
                # 11. Duplicate update ID
                # Pre-insert (client_id, update_hash) into strategy's seen_updates
                cert = json.loads(target_fit_res.metrics["certificate"])
                round_seen = strategy.seen_updates.setdefault(cert["round_id"], set())
                round_seen.add(("client0", cert["update_hash"]))

            elif condition_id == 12:
                # 12. Modified ciphertext
                ct_bytes = bytearray(bytes.fromhex(target_fit_res.metrics["ciphertext_hex"]))
                # Flip random byte
                flip_idx = random.randint(0, len(ct_bytes) - 1)
                ct_bytes[flip_idx] ^= random.randint(1, 255)
                target_fit_res.metrics["ciphertext_hex"] = bytes(ct_bytes).hex()

                variant = attempt_idx % 3
                if variant == 1:
                    # Recompute update_hash in cert without signature
                    cert = json.loads(target_fit_res.metrics["certificate"])
                    cert["update_hash"] = hashlib.sha256(bytes.fromhex(target_fit_res.metrics["nonce_hex"]) + bytes(ct_bytes)).hexdigest()
                    target_fit_res.metrics["certificate"] = json.dumps(cert)
                elif variant == 2:
                    # Recompute update_hash in cert AND re-sign to test AES-GCM decryption failure
                    cert = json.loads(target_fit_res.metrics["certificate"])
                    cert["update_hash"] = hashlib.sha256(bytes.fromhex(target_fit_res.metrics["nonce_hex"]) + bytes(ct_bytes)).hexdigest()
                    target_fit_res.metrics["certificate"] = json.dumps(cert)
                    target_fit_res.metrics["signature"] = sign_certificate(cert, secret_key)

            elif condition_id == 13:
                # 13. Modified nonce
                nonce_bytes = bytearray(bytes.fromhex(target_fit_res.metrics["nonce_hex"]))
                flip_idx = random.randint(0, len(nonce_bytes) - 1)
                nonce_bytes[flip_idx] ^= random.randint(1, 255)
                target_fit_res.metrics["nonce_hex"] = bytes(nonce_bytes).hex()

                variant = attempt_idx % 3
                if variant == 1:
                    cert = json.loads(target_fit_res.metrics["certificate"])
                    cert["update_hash"] = hashlib.sha256(bytes(nonce_bytes) + bytes.fromhex(target_fit_res.metrics["ciphertext_hex"])).hexdigest()
                    target_fit_res.metrics["certificate"] = json.dumps(cert)
                elif variant == 2:
                    cert = json.loads(target_fit_res.metrics["certificate"])
                    cert["update_hash"] = hashlib.sha256(bytes(nonce_bytes) + bytes.fromhex(target_fit_res.metrics["ciphertext_hex"])).hexdigest()
                    target_fit_res.metrics["certificate"] = json.dumps(cert)
                    target_fit_res.metrics["signature"] = sign_certificate(cert, secret_key)

            elif condition_id == 14:
                # 14. Modified AAD
                variant = attempt_idx % 3
                if variant == 0:
                    # Tamper client_id in cert without signature
                    cert = json.loads(target_fit_res.metrics["certificate"])
                    cert["client_id"] = "client_tampered"
                    target_fit_res.metrics["certificate"] = json.dumps(cert)
                elif variant == 1:
                    # Re-sign cert with tampered client_id (triggers wrong_client_id rule)
                    cert = json.loads(target_fit_res.metrics["certificate"])
                    cert["client_id"] = "client99"
                    target_fit_res.metrics["certificate"] = json.dumps(cert)
                    target_fit_res.metrics["signature"] = sign_certificate(cert, secret_key)
                else:
                    # Pass modified AAD directly to decryption stage to trigger AEAD tag mismatch
                    target_aad = compute_aad(1, "client_tampered", base["model_hash"], base["key_context_id"])

            # Run evaluation through 2-stage pipeline
            is_acc, reason = evaluate_update_pipeline(
                strategy=strategy,
                fit_res=target_fit_res,
                client_proxy=client_proxy,
                current_time=target_eval_time,
                decryption_key=target_key,
                expected_aad=target_aad,
            )

            if is_acc:
                accepted_count += 1
            else:
                rejected_count += 1

            reason_distribution[reason] = reason_distribution.get(reason, 0) + 1

    total_time = time.time() - start_time
    avg_time_ms = (total_time / total_attempts) * 1000.0

    # Rates
    if condition_id == 1:
        # For condition 1: legimate acceptance rate
        success_rate = accepted_count / total_attempts
        failure_rate = rejected_count / total_attempts
        attack_success_rate = 0.0
        legitimate_acceptance_rate = success_rate
    else:
        # For attack conditions: attack success rate is accepted_count / total_attempts
        attack_success_rate = accepted_count / total_attempts
        failure_rate = rejected_count / total_attempts
        success_rate = attack_success_rate
        legitimate_acceptance_rate = 0.0

    return {
        "condition_id": condition_id,
        "name": condition_name,
        "attempts": total_attempts,
        "accepted": accepted_count,
        "rejected": rejected_count,
        "success_rate": float(success_rate),
        "failure_rate": float(failure_rate),
        "attack_success_rate": float(attack_success_rate),
        "legitimate_acceptance_rate": float(legitimate_acceptance_rate),
        "rejection_reason_distribution": reason_distribution,
        "seeds": seeds,
        "total_time_seconds": float(total_time),
        "avg_time_per_attempt_ms": float(avg_time_ms),
    }


def main():
    parser = argparse.ArgumentParser(description="SDFL Security Attack Evaluation Harness (E9)")
    parser.add_argument("--attempts_per_seed", type=int, default=200, help="Number of attempts per seed (default: 200)")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 101, 2024, 777, 9999], help="Seeds to use")
    parser.add_argument("--output", type=str, default="results/e9_security_attack_results.json", help="Output JSON path")
    args = parser.parse_args()

    seeds = args.seeds
    attempts_per_seed = args.attempts_per_seed
    total_per_cond = len(seeds) * attempts_per_seed

    conditions = [
        (1, "timely valid update"),
        (2, "expired update"),
        (3, "replayed update"),
        (4, "tampered certificate"),
        (5, "wrong key"),
        (6, "wrong key_context_id"),
        (7, "wrong round_id"),
        (8, "wrong model hash"),
        (9, "cross-round substitution"),
        (10, "post-destruction decryption"),
        (11, "duplicate update ID"),
        (12, "modified ciphertext"),
        (13, "modified nonce"),
        (14, "modified AAD"),
    ]

    print("=" * 80)
    print("SDFL SECURITY ATTACK EVALUATION HARNESS (EXPERIMENT E9)")
    print(f"Running {len(conditions)} conditions | {total_per_cond} attempts/condition ({len(seeds)} seeds x {attempts_per_seed} attempts)")
    print("=" * 80)

    results_by_cond = {}
    harness_start = time.time()

    for cond_id, cond_name in conditions:
        print(f"[{cond_id:2d}/14] Testing '{cond_name}'...", end="", flush=True)
        res = run_condition_tests(
            condition_id=cond_id,
            condition_name=cond_name,
            seeds=seeds,
            attempts_per_seed=attempts_per_seed,
        )
        results_by_cond[str(cond_id)] = res
        print(f" Done ({res['total_time_seconds']:.2f}s) | Accepted: {res['accepted']}/{res['attempts']} | Rejected: {res['rejected']}")

    total_harness_time = time.time() - harness_start

    # Compile JSON Output
    output_data = {
        "experiment": "E9_SDFL_Security_Attack_Evaluation",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_conditions_tested": len(conditions),
        "seeds_used": seeds,
        "attempts_per_condition": total_per_cond,
        "total_attempts_executed": total_per_cond * len(conditions),
        "total_runtime_seconds": float(total_harness_time),
        "summary": {
            "condition_1_legitimate_acceptance_rate": results_by_cond["1"]["legitimate_acceptance_rate"],
            "attack_conditions_max_success_rate": max(
                results_by_cond[str(i)]["attack_success_rate"] for i in range(2, 15)
            ),
            "attack_conditions_overall_defense_rate": min(
                results_by_cond[str(i)]["failure_rate"] for i in range(2, 15)
            ),
        },
        "conditions": results_by_cond,
    }

    # Save JSON
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)

    print("\nMachine-readable results saved to:", args.output)

    # Print Summary Table
    print("\n" + "=" * 105)
    print(f"{'E9 — SDFL SECURITY ATTACK EVALUATION SUMMARY TABLE':^105}")
    print("=" * 105)
    header = f"{'#':<3} | {'Condition Name':<28} | {'Attempts':<8} | {'Accept':<6} | {'Reject':<6} | {'Atk Succ%':<9} | {'Primary Rejection Reason(s)':<30}"
    print(header)
    print("-" * 105)

    for cond_id in range(1, 15):
        r = results_by_cond[str(cond_id)]
        c_name = r["name"]
        att = r["attempts"]
        acc = r["accepted"]
        rej = r["rejected"]
        succ = f"{r['attack_success_rate']*100:.1f}%" if cond_id > 1 else f"{r['legitimate_acceptance_rate']*100:.1f}%*"

        # Formulate top rejection reasons
        reasons_str = ", ".join([f"{k}:{v}" for k, v in sorted(r["rejection_reason_distribution"].items(), key=lambda x: x[1], reverse=True)])
        if len(reasons_str) > 30:
            reasons_str = reasons_str[:27] + "..."

        row = f"{cond_id:<3} | {c_name:<28} | {att:<8} | {acc:<6} | {rej:<6} | {succ:<9} | {reasons_str:<30}"
        print(row)

    print("=" * 105)
    print("* Note: Condition 1 measures legitimate acceptance rate (target: 100%). Conditions 2-14 measure attack success rate (target: 0%).")
    print(f"Total Evaluation Runtime: {total_harness_time:.2f} seconds\n")

    # Check expectations
    c1_ok = results_by_cond["1"]["legitimate_acceptance_rate"] == 1.0
    attacks_ok = all(results_by_cond[str(i)]["attack_success_rate"] == 0.0 for i in range(2, 15))

    if c1_ok and attacks_ok:
        print("✅ ALL EXPECTED OUTCOMES VERIFIED PERFECTLY! (E9 is 100% Ready for the Paper)")
    else:
        print("⚠️ WARNING: Unexpected outcomes detected during evaluation.")


if __name__ == "__main__":
    main()
