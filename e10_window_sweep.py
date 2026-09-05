import os
import sys
import json
import time
import uuid
import math
import hashlib
import numpy as np

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
    write_audit_log,
    server_aggregate
)
from e7_temporal import TemporalCheckpointingSecAgg

class DummyClientProxy:
    def __init__(self, cid):
        self.cid = str(cid)

class DummyFitRes:
    def __init__(self, metrics, num_examples=100):
        self.metrics = metrics
        self.num_examples = num_examples

def generate_mock_weights(seed=None):
    if seed is not None:
        np.random.seed(seed)
    w1 = np.random.randn(16, 8, 3, 3).astype(np.float32) * 0.05
    b1 = np.random.randn(16).astype(np.float32) * 0.01
    return [w1, b1]

def compute_aad_bytes(cert, signature, uid):
    aad_data = {
        "cert": cert,
        "signature": signature,
        "UID_r": uid
    }
    return json.dumps(aad_data, sort_keys=True).encode("utf-8")

def sample_client_latency(client_id, seed=None):
    """
    Simulates realistic heterogeneous clinical computing & network latency:
    - Hospital 0 (Tier-1 Academic Hospital): High-performance GPU workstation (mean=38s, std=6s)
    - Hospital 1 (Regional Medical Center): Mid-tier GPU (mean=72s, std=15s)
    - Hospital 2 (Community Clinic): Constrained GPU / CPU fallback with 15% straggler spike (mean=140s, std=40s; spikes to 350-600s)
    """
    rng = np.random.RandomState(seed)
    if client_id == 0:
        base = rng.normal(38.0, 6.0)
        return max(22.0, base)
    elif client_id == 1:
        base = rng.normal(72.0, 15.0)
        return max(38.0, base)
    else:  # client_id == 2 (straggler prone)
        is_straggler = (rng.rand() < 0.15)
        if is_straggler:
            base = rng.uniform(320.0, 650.0)
        else:
            base = rng.normal(140.0, 35.0)
        return max(65.0, base)

def run_e10_temporal_window_sweep(window_durations=[30, 60, 120, 300, 600, 1200], rounds_per_window=100):
    print("=" * 85)
    print(f"{'E10: TEMPORAL WINDOW ANALYSIS EXPERIMENT':^85}")
    print(f"{'Evaluating Availability vs. Exposure Tradeoff Across Window Durations Tr':^85}")
    print("=" * 85)
    print(f"Sweeping Tr windows: {window_durations} seconds")
    print(f"Rounds per window:   {rounds_per_window} (Total rounds evaluated: {len(window_durations) * rounds_per_window})")
    print("-" * 85)

    results_dir = os.path.join(ROOT_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)
    sweep_log_path = os.path.join(results_dir, "e10_window_log.jsonl")
    if os.path.exists(sweep_log_path):
        os.remove(sweep_log_path)

    secret_key = b"sdfl_coordinator_signing_secret_key_32bytes"
    start_time = time.time()
    sweep_results = {}

    for window_sec in window_durations:
        print(f"\n[Evaluating Window Tr = {window_sec:4d}s] Running {rounds_per_window} rounds...")

        completed_rounds = 0
        total_client_submissions = rounds_per_window * 3
        accepted_client_updates = 0
        rejected_late_updates = 0

        round_latencies = []
        vulnerability_windows = []
        accepted_counts_per_round = []

        for r in range(rounds_per_window):
            round_seed = r * 100 + window_sec
            t_open = 100000.0  # Base simulated virtual epoch start time
            t_expiry = t_open + window_sec
            key_ctx_id = str(uuid.uuid4())
            round_key = generate_round_key()

            cert = create_certificate(
                round_id=r + 1,
                model_hash=hashlib.sha256(f"m_{r}".encode()).hexdigest(),
                participants=["hosp_0", "hosp_1", "hosp_2"],
                key_context_id=key_ctx_id,
                expiry_timestamp=t_expiry
            )
            sig = sign_certificate(cert, secret_key)

            strategy = TemporalCheckpointingSecAgg(
                mu=0.001, C=2.0, sigma=1.5, secret_key=secret_key, window_seconds=window_sec
            )
            strategy.current_key_context_id = key_ctx_id
            strategy.current_Tr = t_expiry
            strategy.round_keys[key_ctx_id] = round_key

            round_accepted_updates = []
            round_client_arrival_times = []

            # Simulate 3 heterogeneous hospital clients
            for cid in range(3):
                client_seed = round_seed + cid
                latency = sample_client_latency(cid, seed=client_seed)
                t_arrival = t_open + latency
                round_client_arrival_times.append(t_arrival)

                # Client encryption
                uid = str(uuid.uuid4())
                aad_bytes = compute_aad_bytes(cert, sig, uid)
                weights = generate_mock_weights(seed=client_seed)
                ct = client_encrypt(weights, round_key, aad=aad_bytes)

                fit_res_metrics = {
                    "nonce_hex": ct["nonce"].hex(),
                    "ciphertext_hex": ct["ciphertext"].hex(),
                    "certificate": json.dumps(cert),
                    "signature": sig,
                    "key_context_id": key_ctx_id,
                    "UID_r": uid
                }
                fit_res = DummyFitRes(fit_res_metrics, num_examples=100)

                # Validate against temporal window
                is_valid, reason = strategy.validate_update(fit_res, current_time=t_arrival)
                if is_valid:
                    accepted_client_updates += 1
                    round_accepted_updates.append((cid, t_arrival, ct, aad_bytes))
                else:
                    if reason == "expired":
                        rejected_late_updates += 1

            accepted_count = len(round_accepted_updates)
            accepted_counts_per_round.append(accepted_count)

            # Quorum check: FL requires >= 2 participating hospital nodes to aggregate
            quorum_met = (accepted_count >= 2)
            if quorum_met:
                completed_rounds += 1
                # Round ends when the last accepted client arrives or at Tr
                effective_round_end = max(t for _, t, _, _ in round_accepted_updates)
                round_duration = effective_round_end - t_open
                round_latencies.append(round_duration)

                # Ciphertext vulnerability exposure window:
                # Duration from when the first encrypted update arrives until key destruction
                first_ciphertext_time = min(t for _, t, _, _ in round_accepted_updates)
                exposure_window = max(0.0, effective_round_end - first_ciphertext_time)
                vulnerability_windows.append(exposure_window)

                # Aggregate and destroy key
                list_of_cts = [{"nonce": ct["nonce"], "ciphertext": ct["ciphertext"]} for _, _, ct, _ in round_accepted_updates]
                aad_list = [aad for _, _, _, aad in round_accepted_updates]
                num_ex_list = [100] * len(list_of_cts)
                _ = server_aggregate(list_of_cts, round_key, num_examples_list=num_ex_list, aad_list=aad_list)
            else:
                # Quorum not met: round aborted at Tr
                round_latencies.append(float(window_sec))
                if round_accepted_updates:
                    first_t = min(t for _, t, _, _ in round_accepted_updates)
                    vulnerability_windows.append(t_expiry - first_t)
                else:
                    vulnerability_windows.append(0.0)

            # In-memory destruction
            destroy_round_key(round_key)

            if r < 3 or r % 50 == 0:
                write_audit_log(sweep_log_path, {
                    "Tr_seconds": window_sec,
                    "round": r + 1,
                    "completed": quorum_met,
                    "accepted_clients": accepted_count,
                    "rejected_stragglers": 3 - accepted_count
                })

        # Calculate statistics for this window
        round_completion_rate = completed_rounds / rounds_per_window
        client_acceptance_rate = accepted_client_updates / total_client_submissions
        straggler_rejection_rate = rejected_late_updates / total_client_submissions

        mean_latency = float(np.mean(round_latencies))
        p50_latency = float(np.median(round_latencies))
        p95_latency = float(np.percentile(round_latencies, 95))

        mean_exposure = float(np.mean(vulnerability_windows))
        p95_exposure = float(np.percentile(vulnerability_windows, 95))

        # Security-Availability Efficiency Index (SAEI):
        # Measures ratio of successful availability to security exposure window
        # Higher score indicates superior Pareto efficiency
        if mean_exposure > 0:
            pareto_index = round((round_completion_rate * 100.0) / (mean_exposure + 1.0), 3)
        else:
            pareto_index = 0.0

        sweep_results[str(window_sec)] = {
            "window_duration_seconds": window_sec,
            "rounds_evaluated": rounds_per_window,
            "round_completion_rate": round_completion_rate,
            "client_acceptance_rate": client_acceptance_rate,
            "straggler_rejection_rate": straggler_rejection_rate,
            "latency": {
                "mean_seconds": round(mean_latency, 2),
                "median_seconds": round(p50_latency, 2),
                "p95_seconds": round(p95_latency, 2)
            },
            "security_exposure_window": {
                "mean_seconds": round(mean_exposure, 2),
                "p95_seconds": round(p95_exposure, 2)
            },
            "mean_accepted_clients_per_round": round(float(np.mean(accepted_counts_per_round)), 2),
            "pareto_efficiency_index": pareto_index
        }

        print(f"  Completion: {round_completion_rate*100:5.1f}% | Client Acc: {client_acceptance_rate*100:5.1f}% | "
              f"Late Rej: {straggler_rejection_rate*100:5.1f}% | Mean Latency: {mean_latency:6.1f}s | "
              f"Mean Exposure: {mean_exposure:5.1f}s | Pareto: {pareto_index}")

    elapsed_time = time.time() - start_time

    # Find optimal Pareto window
    optimal_window = max(sweep_results.keys(), key=lambda k: sweep_results[k]["pareto_efficiency_index"])

    output_data = {
        "experiment": "E10_Temporal_Window_Sweep",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rounds_per_window": rounds_per_window,
        "optimal_window_seconds": int(optimal_window),
        "execution_time_seconds": round(elapsed_time, 2),
        "window_metrics": sweep_results
    }

    results_json_path = os.path.join(results_dir, "e10_window_results.json")
    with open(results_json_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print("\n" + "=" * 85)
    print(f"{'E10 SWEEP EXPERIMENT COMPLETED SUCCESSFULLY':^85}")
    print(f"Saved results to: {results_json_path}")
    print(f"Optimal Pareto Operating Window: Tr = {optimal_window} seconds")
    print("=" * 85 + "\n")

    return output_data

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run E10 Temporal Window Analysis Experiment")
    parser.add_argument("--rounds", type=int, default=100, help="Number of simulated rounds per window")
    args = parser.parse_args()

    run_e10_temporal_window_sweep(rounds_per_window=args.rounds)
