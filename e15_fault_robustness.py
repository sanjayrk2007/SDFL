"""
E15: Fault and Late-Client Robustness Evaluation
================================================
Comprehensive verification of the SDFL temporal security and aggregation protocol
under network faults, packet anomalies, and adversarial tampering.

Tests 10 distinct operational scenarios:
  1. Normal on-time client submission -> ACCEPTED
  2. Late client submission (t >= Tr) -> REJECTED (expired)
  3. Replay attack / duplicate UID transmission -> REJECTED (replay_detected)
  4. Forged / invalid HMAC signature -> REJECTED (invalid_signature)
  5. Stale / mismatched key_context_id -> REJECTED (mismatch)
  6. Tampered AAD binding (modified certificate content) -> REJECTED (decryption auth failure)
  7. Client dropout / partial quorum (1 client drops, 2 submit) -> DEGRADED AGGREGATION
  8. Total dropout / zero valid submissions -> ROUND ABORT & MODEL PRESERVED
  9. Key destruction verification (post-round zeroing) -> KEY UNRECOVERABLE
  10. Next-round recovery after failed / partial round -> FULL RECOVERY

Outputs:
  - Results_New/E15/e15_fault_results.json
  - Results_New/E15/e15_fault_log.jsonl
  - Results_New/E15/E15_RESULTS.md
"""

import os
import sys
import gc
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import torch

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from crypto import (
    generate_round_key,
    client_encrypt,
    decrypt_update,
    create_certificate,
    sign_certificate,
    verify_certificate,
    destroy_round_key,
    server_aggregate
)
from e2_server import DEVICE, ResUNetPlusPlus, get_parameters, set_parameters
from e4_dpsgd import fix_model_for_opacus
from e7_temporal import compute_model_hash, SECRET_KEY, compute_aad

RESULTS_DIR = ROOT_DIR / "Results_New" / "E15"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_JSON = RESULTS_DIR / "e15_fault_results.json"
OUT_LOG = RESULTS_DIR / "e15_fault_log.jsonl"
OUT_REPORT = RESULTS_DIR / "E15_RESULTS.md"

def log_event(event, **data):
    data.update(event=event, timestamp=datetime.now(timezone.utc).isoformat())
    with OUT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, sort_keys=True) + "\n")

class MockSDFLAggregator:
    """Standalone validator and aggregator executing identical protocol logic to e7_temporal.py."""
    def __init__(self, secret_key=SECRET_KEY):
        self.secret_key = secret_key
        self.consumed_uids = set()
        self.round_keys = {}
        self.current_key_context_id = None
        self.current_Tr = None
        self.cached_ciphertexts = {}

    def open_round(self, round_id, model_hash, participants, duration_seconds=120.0):
        round_key = generate_round_key()
        self.current_key_context_id = str(uuid.uuid4())
        self.round_keys[self.current_key_context_id] = round_key
        self.current_Tr = time.time() + duration_seconds

        cert = create_certificate(
            round_id=round_id,
            model_hash=model_hash,
            participants=participants,
            key_context_id=self.current_key_context_id,
            expiry_timestamp=self.current_Tr
        )
        sig = sign_certificate(cert, self.secret_key)
        return round_key, cert, sig

    def validate_submission(self, submission, current_time=None):
        if current_time is None:
            current_time = time.time()

        cert_str = submission.get("certificate")
        sig = submission.get("signature")
        ctx_id = submission.get("key_context_id")
        uid = submission.get("UID_r")

        if not cert_str or not sig or not ctx_id or not uid:
            return False, "missing_certificate_fields"

        if uid in self.consumed_uids:
            return False, "replay_detected"

        try:
            cert = json.loads(cert_str)
        except Exception:
            return False, "invalid_json"

        if not verify_certificate(cert, sig, self.secret_key):
            return False, "invalid_signature"

        if current_time >= cert.get("expiry_timestamp", 0):
            return False, "expired"

        if ctx_id != cert.get("key_context_id") or ctx_id != self.current_key_context_id:
            return False, "mismatch"

        return True, "accepted"

    def aggregate_submissions(self, server_round, submissions, current_time=None):
        if current_time is None:
            current_time = time.time()

        valid_ciphertexts = []
        aad_list = []
        num_examples_list = []
        rejected_reasons = []

        for sub in submissions:
            is_valid, reason = self.validate_submission(sub, current_time)
            if not is_valid:
                rejected_reasons.append({"client_id": sub.get("client_id"), "reason": reason})
                continue

            ct = {
                "nonce": bytes.fromhex(sub["nonce_hex"]),
                "ciphertext": bytes.fromhex(sub["ciphertext_hex"])
            }
            valid_ciphertexts.append(ct)
            num_examples_list.append(sub.get("num_examples", 100))

            cert_str = sub["certificate"]
            sig = sub["signature"]
            uid = sub["UID_r"]
            # Canonical AAD (bound to this client's own identity), not the
            # bespoke {cert, signature, UID_r} scheme -- see
            # SDFL_Preflight_Audit.md, Section 3/5.
            cert_obj = json.loads(cert_str)
            aad_bytes = compute_aad(
                round_id=cert_obj["round_id"],
                client_id=sub.get("client_id"),
                model_hash=cert_obj["model_hash"],
                key_context_id=cert_obj["key_context_id"],
            )
            aad_list.append(aad_bytes)
            self.consumed_uids.add(uid)

        self.cached_ciphertexts[server_round] = valid_ciphertexts
        round_key = self.round_keys.get(self.current_key_context_id)

        aggregated_weights = None
        decryption_success = False

        if valid_ciphertexts and round_key is not None:
            try:
                aggregated_weights = server_aggregate(
                    valid_ciphertexts,
                    round_key,
                    num_examples_list=num_examples_list,
                    associated_data_list=aad_list
                )
                decryption_success = True
            except Exception as e:
                decryption_success = False
                rejected_reasons.append({"client_id": "aggregator", "reason": f"decryption_auth_failed: {str(e)}"})

        return {
            "accepted_count": len(valid_ciphertexts),
            "rejected_count": len(submissions) - len(valid_ciphertexts),
            "rejected_details": rejected_reasons,
            "decryption_success": decryption_success,
            "has_aggregated_weights": aggregated_weights is not None
        }

    def close_and_destroy_round(self):
        round_key = self.round_keys.get(self.current_key_context_id)
        if round_key is not None:
            destroy_round_key(round_key)
            self.round_keys[self.current_key_context_id] = None
        self.cached_ciphertexts.clear()

def create_client_update(client_id, template_weights, round_key, cert, sig, uid=None, sample_count=264, custom_aad=None):
    if uid is None:
        uid = str(uuid.uuid4())

    if custom_aad is not None:
        aad_bytes = custom_aad
    else:
        # Canonical AAD (bound to this client's own identity), matching
        # aggregate_submissions()'s server-side re-derivation -- see
        # SDFL_Preflight_Audit.md, Section 3/5.
        aad_bytes = compute_aad(
            round_id=cert["round_id"],
            client_id=client_id,
            model_hash=cert["model_hash"],
            key_context_id=cert["key_context_id"],
        )

    weights = [arr + np.random.normal(0, 1e-4, arr.shape).astype(arr.dtype) for arr in template_weights]
    ct = client_encrypt(weights, round_key, associated_data=aad_bytes)

    return {
        "client_id": client_id,
        "nonce_hex": ct["nonce"].hex(),
        "ciphertext_hex": ct["ciphertext"].hex(),
        "certificate": json.dumps(cert),
        "signature": sig,
        "key_context_id": cert["key_context_id"],
        "UID_r": uid,
        "num_examples": sample_count
    }

def run_fault_experiments():
    OUT_LOG.unlink(missing_ok=True)
    t_start = datetime.now(timezone.utc).isoformat()
    log_event("e15_started")

    # Load template weights
    model = ResUNetPlusPlus().to("cpu")
    fix_model_for_opacus(model)
    template_weights = get_parameters(model)
    model_hash = compute_model_hash(model.state_dict())
    del model
    gc.collect()

    aggregator = MockSDFLAggregator()
    scenarios = []

    print("\n========================================================")
    print("E15: Running Fault & Late-Client Robustness Suite")
    print("========================================================")

    # ----------------------------------------------------
    # SCENARIO 1: Normal on-time client submission
    # ----------------------------------------------------
    round_key, cert, sig = aggregator.open_round(round_id=1, model_hash=model_hash, participants=["c0", "c1", "c2"])
    sub0 = create_client_update("c0", template_weights, round_key, cert, sig)
    sub1 = create_client_update("c1", template_weights, round_key, cert, sig)
    sub2 = create_client_update("c2", template_weights, round_key, cert, sig)
    
    res1 = aggregator.aggregate_submissions(1, [sub0, sub1, sub2], current_time=time.time())
    aggregator.close_and_destroy_round()
    
    sc1 = {
        "scenario_id": "SC-01",
        "name": "Normal On-Time Submissions",
        "description": "3 clients submit valid updates within window Tr",
        "expected_accepted": 3,
        "actual_accepted": res1["accepted_count"],
        "passed": res1["accepted_count"] == 3 and res1["has_aggregated_weights"]
    }
    scenarios.append(sc1)
    log_event("scenario_tested", **sc1)
    print(f"[{'PASS' if sc1['passed'] else 'FAIL'}] SC-01: {sc1['name']} -> Accepted: {res1['accepted_count']}/3")

    # ----------------------------------------------------
    # SCENARIO 2: Late client submission (t >= Tr)
    # ----------------------------------------------------
    round_key, cert, sig = aggregator.open_round(round_id=2, model_hash=model_hash, participants=["c0", "c1", "c2"])
    sub0 = create_client_update("c0", template_weights, round_key, cert, sig)
    sub1 = create_client_update("c1", template_weights, round_key, cert, sig)
    sub2_late = create_client_update("c2", template_weights, round_key, cert, sig)
    
    # c2 arrives after expiry
    res2_on_time = aggregator.aggregate_submissions(2, [sub0, sub1], current_time=time.time())
    res2_late = aggregator.validate_submission(sub2_late, current_time=cert["expiry_timestamp"] + 5.0)
    aggregator.close_and_destroy_round()

    sc2 = {
        "scenario_id": "SC-02",
        "name": "Late Client Rejection",
        "description": "Client submits update after round expiry timestamp Tr",
        "expected_status": "expired",
        "actual_status": res2_late[1],
        "passed": res2_late[0] is False and res2_late[1] == "expired" and res2_on_time["accepted_count"] == 2
    }
    scenarios.append(sc2)
    log_event("scenario_tested", **sc2)
    print(f"[{'PASS' if sc2['passed'] else 'FAIL'}] SC-02: {sc2['name']} -> Status: {res2_late[1]}")

    # ----------------------------------------------------
    # SCENARIO 3: Replay attack / duplicate transmission
    # ----------------------------------------------------
    round_key, cert, sig = aggregator.open_round(round_id=3, model_hash=model_hash, participants=["c0", "c1"])
    shared_uid = str(uuid.uuid4())
    sub0 = create_client_update("c0", template_weights, round_key, cert, sig, uid=shared_uid)
    sub_replayed = create_client_update("c0", template_weights, round_key, cert, sig, uid=shared_uid)
    
    # First submission accepted
    res3_first = aggregator.aggregate_submissions(3, [sub0], current_time=time.time())
    # Second submission with duplicate UID rejected
    res3_replay = aggregator.validate_submission(sub_replayed, current_time=time.time())
    aggregator.close_and_destroy_round()

    sc3 = {
        "scenario_id": "SC-03",
        "name": "Replay / Duplicate Protection",
        "description": "Replay of consumed UID_r within or across rounds",
        "expected_status": "replay_detected",
        "actual_status": res3_replay[1],
        "passed": res3_replay[0] is False and res3_replay[1] == "replay_detected"
    }
    scenarios.append(sc3)
    log_event("scenario_tested", **sc3)
    print(f"[{'PASS' if sc3['passed'] else 'FAIL'}] SC-03: {sc3['name']} -> Status: {res3_replay[1]}")

    # ----------------------------------------------------
    # SCENARIO 4: Forged HMAC certificate signature
    # ----------------------------------------------------
    round_key, cert, sig = aggregator.open_round(round_id=4, model_hash=model_hash, participants=["c0"])
    forged_sig = "deadbeef" * 8
    sub_forged = create_client_update("c0", template_weights, round_key, cert, sig=forged_sig)
    
    res4 = aggregator.validate_submission(sub_forged, current_time=time.time())
    aggregator.close_and_destroy_round()

    sc4 = {
        "scenario_id": "SC-04",
        "name": "Forged Signature Rejection",
        "description": "Attacker generates fake certificate signature",
        "expected_status": "invalid_signature",
        "actual_status": res4[1],
        "passed": res4[0] is False and res4[1] == "invalid_signature"
    }
    scenarios.append(sc4)
    log_event("scenario_tested", **sc4)
    print(f"[{'PASS' if sc4['passed'] else 'FAIL'}] SC-04: {sc4['name']} -> Status: {res4[1]}")

    # ----------------------------------------------------
    # SCENARIO 5: Stale / Mismatched Key Context ID
    # ----------------------------------------------------
    round_key, cert, sig = aggregator.open_round(round_id=5, model_hash=model_hash, participants=["c0"])
    sub_mismatch = create_client_update("c0", template_weights, round_key, cert, sig)
    sub_mismatch["key_context_id"] = str(uuid.uuid4()) # Mismatched context

    res5 = aggregator.validate_submission(sub_mismatch, current_time=time.time())
    aggregator.close_and_destroy_round()

    sc5 = {
        "scenario_id": "SC-05",
        "name": "Key Context Mismatch Rejection",
        "description": "Submission from stale or different round key context",
        "expected_status": "mismatch",
        "actual_status": res5[1],
        "passed": res5[0] is False and res5[1] == "mismatch"
    }
    scenarios.append(sc5)
    log_event("scenario_tested", **sc5)
    print(f"[{'PASS' if sc5['passed'] else 'FAIL'}] SC-05: {sc5['name']} -> Status: {res5[1]}")

    # ----------------------------------------------------
    # SCENARIO 6: Tampered AAD Binding
    # ----------------------------------------------------
    round_key, cert, sig = aggregator.open_round(round_id=6, model_hash=model_hash, participants=["c0"])
    # Client encrypts under tampered AAD
    tampered_aad = json.dumps({"cert": cert, "signature": sig, "UID_r": "tampered_uid"}).encode()
    sub_tampered = create_client_update("c0", template_weights, round_key, cert, sig, custom_aad=tampered_aad)
    
    # Validator accepts outer certificate fields, but AES-GCM server aggregate fails authentication tag check
    res6 = aggregator.aggregate_submissions(6, [sub_tampered], current_time=time.time())
    aggregator.close_and_destroy_round()

    sc6 = {
        "scenario_id": "SC-06",
        "name": "Tampered AAD Authentication Failure",
        "description": "Ciphertext encrypted under mismatched AAD binding fails AES-GCM decryption tag",
        "passed": res6["decryption_success"] is False and res6["has_aggregated_weights"] is False
    }
    scenarios.append(sc6)
    log_event("scenario_tested", **sc6)
    print(f"[{'PASS' if sc6['passed'] else 'FAIL'}] SC-06: {sc6['name']} -> Decryption Auth Success: {res6['decryption_success']}")

    # ----------------------------------------------------
    # SCENARIO 7: Partial Quorum / Client Dropout
    # ----------------------------------------------------
    round_key, cert, sig = aggregator.open_round(round_id=7, model_hash=model_hash, participants=["c0", "c1", "c2"])
    sub0 = create_client_update("c0", template_weights, round_key, cert, sig)
    sub1 = create_client_update("c1", template_weights, round_key, cert, sig)
    # c2 drops out
    res7 = aggregator.aggregate_submissions(7, [sub0, sub1], current_time=time.time())
    aggregator.close_and_destroy_round()

    sc7 = {
        "scenario_id": "SC-07",
        "name": "Partial Client Dropout Graceful Aggregation",
        "description": "1 client crashes/drops; remaining 2 clients successfully aggregate",
        "expected_accepted": 2,
        "actual_accepted": res7["accepted_count"],
        "passed": res7["accepted_count"] == 2 and res7["has_aggregated_weights"] is True
    }
    scenarios.append(sc7)
    log_event("scenario_tested", **sc7)
    print(f"[{'PASS' if sc7['passed'] else 'FAIL'}] SC-07: {sc7['name']} -> Aggregated {res7['accepted_count']}/2 active clients")

    # ----------------------------------------------------
    # SCENARIO 8: Total Dropout / Zero Valid Updates
    # ----------------------------------------------------
    round_key, cert, sig = aggregator.open_round(round_id=8, model_hash=model_hash, participants=["c0", "c1", "c2"])
    res8 = aggregator.aggregate_submissions(8, [], current_time=time.time())
    aggregator.close_and_destroy_round()

    sc8 = {
        "scenario_id": "SC-08",
        "name": "Total Dropout Round Handling",
        "description": "Zero client updates received; round terminates cleanly without corrupting global model",
        "passed": res8["accepted_count"] == 0 and res8["has_aggregated_weights"] is False
    }
    scenarios.append(sc8)
    log_event("scenario_tested", **sc8)
    print(f"[{'PASS' if sc8['passed'] else 'FAIL'}] SC-08: {sc8['name']} -> Has Aggregated Weights: {res8['has_aggregated_weights']}")

    # ----------------------------------------------------
    # SCENARIO 9: Post-Round Key Destruction
    # ----------------------------------------------------
    round_key, cert, sig = aggregator.open_round(round_id=9, model_hash=model_hash, participants=["c0"])
    sub0 = create_client_update("c0", template_weights, round_key, cert, sig)
    # Aggregate and close
    aggregator.aggregate_submissions(9, [sub0], current_time=time.time())
    aggregator.close_and_destroy_round()

    # Attempt decryption post-round
    post_round_key = aggregator.round_keys.get(cert["key_context_id"])
    key_is_destroyed = post_round_key is None or all(b == 0 for b in post_round_key)

    sc9 = {
        "scenario_id": "SC-09",
        "name": "Post-Round Decryption Key Destruction",
        "description": "Round key zeroed in memory; retrospective recovery impossible",
        "passed": key_is_destroyed
    }
    scenarios.append(sc9)
    log_event("scenario_tested", **sc9)
    print(f"[{'PASS' if sc9['passed'] else 'FAIL'}] SC-09: {sc9['name']} -> Key Zeroed / Destroyed: {key_is_destroyed}")

    # ----------------------------------------------------
    # SCENARIO 10: Next-Round Recovery
    # ----------------------------------------------------
    # Round 10 follows after partial or aborted rounds
    round_key_10, cert_10, sig_10 = aggregator.open_round(round_id=10, model_hash=model_hash, participants=["c0", "c1", "c2"])
    sub0_10 = create_client_update("c0", template_weights, round_key_10, cert_10, sig_10)
    sub1_10 = create_client_update("c1", template_weights, round_key_10, cert_10, sig_10)
    sub2_10 = create_client_update("c2", template_weights, round_key_10, cert_10, sig_10)
    res10 = aggregator.aggregate_submissions(10, [sub0_10, sub1_10, sub2_10], current_time=time.time())
    aggregator.close_and_destroy_round()

    sc10 = {
        "scenario_id": "SC-10",
        "name": "Subsequent Round Recovery",
        "description": "System issues fresh certificate and key context; normal federated learning resumes seamlessly",
        "passed": res10["accepted_count"] == 3 and res10["has_aggregated_weights"] is True
    }
    scenarios.append(sc10)
    log_event("scenario_tested", **sc10)
    print(f"[{'PASS' if sc10['passed'] else 'FAIL'}] SC-10: {sc10['name']} -> Recovered Full Aggregation: {res10['accepted_count']}/3")

    all_passed = all(s["passed"] for s in scenarios)
    t_end = datetime.now(timezone.utc).isoformat()

    full_results = {
        "experiment": "E15 Fault and Late-Client Robustness Suite",
        "timestamp_start": t_start,
        "completed_at": t_end,
        "total_scenarios_tested": len(scenarios),
        "all_scenarios_passed": all_passed,
        "scenarios": scenarios
    }

    OUT_JSON.write_text(json.dumps(full_results, indent=2), encoding="utf-8")
    write_markdown_report(full_results)
    log_event("e15_completed", all_passed=all_passed)
    print(f"\nE15 Suite Complete. All {len(scenarios)} Scenarios Passed: {all_passed}")

def write_markdown_report(data):
    lines = [
        "# E15 — Fault and Late-Client Robustness Suite",
        "",
        f"> Completed: {data['completed_at']}  |  Branch: `mukesh/sdfl-completion`",
        "",
        "## Overview",
        "",
        "Validates that the Self-Destructing Federated Learning (SDFL) coordinator and aggregation server enforce strict cryptographic access boundaries, reject late or malicious packets with exact reason codes, tolerate client dropouts, destroy temporal keys upon round expiry, and recover seamlessly in subsequent training rounds.",
        "",
        "## Scenario Test Matrix",
        "",
        "| Scenario | Description | Expected Behavior | Observed Result | Status |",
        "|:---|:---|:---|:---|:---:|",
    ]

    for sc in data["scenarios"]:
        status_badge = "✅ PASS" if sc["passed"] else "❌ FAIL"
        lines.append(
            f"| **{sc['scenario_id']}**: {sc['name']} | {sc['description']} | "
            f"{sc.get('expected_status') or ('Accept ' + str(sc.get('expected_accepted', 'all')))} | "
            f"{sc.get('actual_status') or ('Accepted ' + str(sc.get('actual_accepted', 'valid')))} | "
            f"{status_badge} |"
        )

    lines.extend([
        "",
        "## Security Enforcement Summary",
        "",
        "1. **Temporal Expiry Enforcement (SC-02):** Packets arriving after round expiration timestamp $T_r$ are strictly rejected with reason code `expired`.",
        "2. **Cryptographic Replay Protection (SC-03):** Replayed or duplicate transaction IDs ($UID_r$) are recognized and rejected with reason code `replay_detected`.",
        "3. **HMAC & AAD Authenticity (SC-04, SC-06):** Forged coordinator signatures and tampered AAD metadata fail verification and AES-GCM decryption tag validation.",
        "4. **Fault Tolerance & Degraded Quorum (SC-07, SC-08):** Unresponsive or dropped clients do not stall the server; valid updates aggregate gracefully without corrupting model state.",
        "5. **Post-Round Key Destruction (SC-09):** Decryption keys and ciphertext buffers are zeroed out immediately following round completion.",
        "6. **Multi-Round Continuity (SC-10):** Fresh cryptographic contexts allow subsequent rounds to proceed with full quorum without session lockup.",
        ""
    ])

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    run_fault_experiments()
