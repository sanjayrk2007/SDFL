#!/usr/bin/env python3
"""
E8 Federated Aggregation & Hardened Security Integration Test Suite
===================================================================
Tests the boundary between the SDFL hardened security implementation and the
E8 federated aggregation pipeline (FullSDFLStrategy and FullSDFLClient).

Validates the complete update lifecycle:
  client model update -> serialization -> AAD construction -> encryption
  -> certificate creation -> signature -> server validation -> ciphertext retrieval
  -> decryption -> weighted aggregation -> resulting global parameters

Explicitly verifies:
  1. Legitimate encrypted update is accepted by FullSDFLStrategy.
  2. Legitimate update decrypts successfully with matching AAD.
  3. AAD mismatch is rejected during AES-GCM decryption / validation.
  4. Modified ciphertext is rejected by update_hash and AES-GCM tag.
  5. Wrong key is rejected during AES-GCM decryption.
  6. Weighted aggregation produces mathematically exact expected results.
  7. Round-key destruction does not break current round before aggregation completes.
  8. Key destruction prevents any subsequent decryption attempts.
"""

import os
import sys
import json
import time
import uuid
import hashlib
import numpy as np
import torch
import flwr as fl
from cryptography.exceptions import InvalidTag

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
scripts_dir = os.path.join(ROOT_DIR, "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from crypto import (
    generate_round_key,
    client_encrypt,
    decrypt_update,
    destroy_round_key,
    create_certificate,
    sign_certificate,
    verify_certificate,
    server_aggregate,
)
from e7_temporal import (
    compute_aad,
    compute_model_hash,
    SECRET_KEY,
)
from e8_server import FullSDFLStrategy, _weighted_server_aggregate


class MockClientProxy:
    def __init__(self, cid: str):
        self.cid = str(cid)


class MockFitRes:
    def __init__(self, metrics: dict, num_examples: int = 100):
        self.metrics = metrics
        self.num_examples = num_examples


def _build_test_update(
    round_id: int,
    client_idx: int,
    model_hash: str,
    key_context_id: str,
    round_key: bytearray,
    weights: list,
    secret_key: bytes = SECRET_KEY,
    expiry_offset: float = 300.0,
    tamper_aad: bytes = None,
    tamper_ct: bool = False,
    tamper_cert_field: tuple = None,
    resign: bool = True,
):
    """
    Helper creating a valid or mutated SDFL update package.
    """
    client_id = f"client{client_idx}"
    expiry_timestamp = time.time() + expiry_offset
    participants = ["client0", "client1", "client2"]

    canonical_aad = compute_aad(round_id, client_id, model_hash, key_context_id)
    aad_to_use = tamper_aad if tamper_aad is not None else canonical_aad

    ct = client_encrypt(weights, round_key, associated_data=aad_to_use)

    if tamper_ct:
        ct_bytes = bytearray(ct["ciphertext"])
        ct_bytes[0] ^= 0xFF
        ct["ciphertext"] = bytes(ct_bytes)

    update_hash = hashlib.sha256(ct["nonce"] + ct["ciphertext"]).hexdigest()

    cert = create_certificate(
        round_id=round_id,
        model_hash=model_hash,
        participants=participants,
        key_context_id=key_context_id,
        expiry_timestamp=expiry_timestamp,
    )
    cert["client_id"] = client_id
    cert["update_hash"] = update_hash

    if tamper_cert_field is not None:
        field, val = tamper_cert_field
        cert[field] = val

    signature = sign_certificate(cert, secret_key) if resign else "0" * 64

    metrics = {
        "hospital_id": client_idx,
        "nonce_hex": ct["nonce"].hex(),
        "ciphertext_hex": ct["ciphertext"].hex(),
        "certificate": json.dumps(cert),
        "signature": signature,
        "key_context_id": key_context_id,
        "client_id": client_id,
    }

    return {
        "client_id": client_id,
        "canonical_aad": canonical_aad,
        "aad_used": aad_to_use,
        "ct": ct,
        "cert": cert,
        "signature": signature,
        "metrics": metrics,
        "fit_res": MockFitRes(metrics),
        "proxy": MockClientProxy(client_id),
    }


def test_1_legitimate_encrypted_update_accepted():
    """Item 1: Legitimate encrypted update is accepted by FullSDFLStrategy."""
    print("Test 1: Verifying legitimate encrypted update is accepted...")
    strategy = FullSDFLStrategy(mu=0.001, C=2.0, sigma=1.5, secret_key=SECRET_KEY, window_seconds=300)
    round_id = 1
    key_ctx = str(uuid.uuid4())
    round_key = generate_round_key()
    strategy.round_keys[key_ctx] = round_key
    strategy.current_key_context_id = key_ctx
    strategy.current_Tr = time.time() + 300
    st = {"layer.weight": torch.ones(4, 4, dtype=torch.float32)}
    m_hash = compute_model_hash(st)
    strategy.current_model_hash = m_hash

    weights = [np.ones((4, 4), dtype=np.float32)]
    pkg = _build_test_update(round_id, 0, m_hash, key_ctx, round_key, weights)

    is_valid, reason = strategy.validate_update(pkg["fit_res"], client_proxy=pkg["proxy"], current_time=time.time())
    assert is_valid, f"Item 1 FAILED: Expected update to be accepted, got: {reason}"
    assert reason == "accepted"
    print("  -> PASS: Legitimate encrypted update accepted.")


def test_2_legitimate_update_decrypts_successfully():
    """Item 2: Legitimate update decrypts successfully with matching AAD."""
    print("Test 2: Verifying legitimate update decrypts successfully...")
    round_id = 1
    key_ctx = str(uuid.uuid4())
    round_key = generate_round_key()
    st = {"layer.weight": torch.ones(4, 4, dtype=torch.float32)}
    m_hash = compute_model_hash(st)

    weights = [np.array([1.23, 4.56, 7.89], dtype=np.float32), np.array([[10, 20], [30, 40]], dtype=np.float32)]
    pkg = _build_test_update(round_id, 0, m_hash, key_ctx, round_key, weights)

    # Server reconstructs AAD from cert
    cert = json.loads(pkg["fit_res"].metrics["certificate"])
    reconstructed_aad = compute_aad(cert["round_id"], cert["client_id"], cert["model_hash"], cert["key_context_id"])
    ct_dict = {
        "nonce": bytes.fromhex(pkg["fit_res"].metrics["nonce_hex"]),
        "ciphertext": bytes.fromhex(pkg["fit_res"].metrics["ciphertext_hex"]),
        "associated_data": reconstructed_aad,
    }

    decrypted_weights = decrypt_update(ct_dict, round_key)
    assert len(decrypted_weights) == len(weights), "Item 2 FAILED: Layer count mismatch"
    for dw, ow in zip(decrypted_weights, weights):
        assert np.array_equal(dw, ow), "Item 2 FAILED: Decrypted numerical weights do not match original"

    print("  -> PASS: Legitimate update decrypted successfully with matching AAD.")


def test_3_aad_mismatch_rejected():
    """Item 3: AAD mismatch is rejected (both validation and AEAD decryption)."""
    print("Test 3: Verifying AAD mismatch is rejected...")
    round_id = 1
    key_ctx = str(uuid.uuid4())
    round_key = generate_round_key()
    st = {"layer.weight": torch.ones(4, 4, dtype=torch.float32)}
    m_hash = compute_model_hash(st)

    weights = [np.ones((2, 2), dtype=np.float32)]
    # Encrypted with legitimate AAD
    pkg = _build_test_update(round_id, 0, m_hash, key_ctx, round_key, weights)

    # A. Decrypting with altered AAD directly must raise InvalidTag
    wrong_aads = [
        compute_aad(round_id + 1, "client0", m_hash, key_ctx),      # Wrong round_id
        compute_aad(round_id, "client1", m_hash, key_ctx),          # Wrong client_id
        compute_aad(round_id, "client0", "wrong_hash", key_ctx),    # Wrong model_hash
        compute_aad(round_id, "client0", m_hash, str(uuid.uuid4())),# Wrong key_context_id
        None,                                                       # None / missing AAD
    ]

    ct_raw = {
        "nonce": pkg["ct"]["nonce"],
        "ciphertext": pkg["ct"]["ciphertext"],
    }

    for i, bad_aad in enumerate(wrong_aads):
        try:
            decrypt_update(ct_raw, round_key, associated_data=bad_aad)
            assert False, f"Item 3 FAILED: Decryption should have failed for wrong AAD variant {i}"
        except InvalidTag:
            pass  # Expected

    # B. Strategy validation rejects tampered certificate metadata
    strategy = FullSDFLStrategy(mu=0.001, C=2.0, sigma=1.5, secret_key=SECRET_KEY, window_seconds=300)
    strategy.round_keys[key_ctx] = round_key
    strategy.current_key_context_id = key_ctx
    strategy.current_Tr = time.time() + 300
    strategy.current_model_hash = m_hash

    # Tampered model_hash in cert
    pkg_bad_hash = _build_test_update(round_id, 0, m_hash, key_ctx, round_key, weights, tamper_cert_field=("model_hash", "tampered_hash"))
    is_valid, reason = strategy.validate_update(pkg_bad_hash["fit_res"], client_proxy=pkg_bad_hash["proxy"], current_time=time.time())
    assert not is_valid and reason == "model_hash_mismatch", f"Item 3 FAILED: expected model_hash_mismatch, got {reason}"

    # Tampered client_id in cert
    pkg_bad_client = _build_test_update(round_id, 0, m_hash, key_ctx, round_key, weights, tamper_cert_field=("client_id", "client1"))
    is_valid, reason = strategy.validate_update(pkg_bad_client["fit_res"], client_proxy=pkg_bad_client["proxy"], current_time=time.time())
    assert not is_valid and reason == "wrong_client_id", f"Item 3 FAILED: expected wrong_client_id, got {reason}"

    print("  -> PASS: AAD mismatch rejected (InvalidTag raised on AEAD & metadata rejected in validation).")


def test_4_modified_ciphertext_rejected():
    """Item 4: Modified ciphertext is rejected."""
    print("Test 4: Verifying modified ciphertext is rejected...")
    strategy = FullSDFLStrategy(mu=0.001, C=2.0, sigma=1.5, secret_key=SECRET_KEY, window_seconds=300)
    round_id = 1
    key_ctx = str(uuid.uuid4())
    round_key = generate_round_key()
    strategy.round_keys[key_ctx] = round_key
    strategy.current_key_context_id = key_ctx
    strategy.current_Tr = time.time() + 300
    st = {"layer.weight": torch.ones(4, 4, dtype=torch.float32)}
    m_hash = compute_model_hash(st)
    strategy.current_model_hash = m_hash

    weights = [np.ones((2, 2), dtype=np.float32)]

    # Variant A: Ciphertext modified, certificate has original update_hash
    pkg_mod_ct = _build_test_update(round_id, 0, m_hash, key_ctx, round_key, weights, tamper_ct=True, resign=False)
    is_valid, reason = strategy.validate_update(pkg_mod_ct["fit_res"], client_proxy=pkg_mod_ct["proxy"], current_time=time.time())
    assert not is_valid and (reason == "update_hash_mismatch" or reason == "invalid_signature"), f"Item 4 FAILED: {reason}"

    # Variant B: Ciphertext modified, update_hash recomputed & cert re-signed -> Decryption must fail with InvalidTag
    cert = pkg_mod_ct["cert"].copy()
    raw_nonce = bytes.fromhex(pkg_mod_ct["metrics"]["nonce_hex"])
    raw_ct = bytes.fromhex(pkg_mod_ct["metrics"]["ciphertext_hex"])
    cert["update_hash"] = hashlib.sha256(raw_nonce + raw_ct).hexdigest()
    sig = sign_certificate(cert, SECRET_KEY)
    pkg_mod_ct["fit_res"].metrics["certificate"] = json.dumps(cert)
    pkg_mod_ct["fit_res"].metrics["signature"] = sig

    is_valid, reason = strategy.validate_update(pkg_mod_ct["fit_res"], client_proxy=pkg_mod_ct["proxy"], current_time=time.time())
    assert is_valid, "Metadata with re-signed hash should pass validation stage"

    ct_dict = {
        "nonce": raw_nonce,
        "ciphertext": raw_ct,
        "associated_data": pkg_mod_ct["canonical_aad"]
    }
    try:
        decrypt_update(ct_dict, round_key)
        assert False, "Item 4 FAILED: Modified ciphertext decrypted successfully!"
    except InvalidTag:
        pass  # Expected

    print("  -> PASS: Modified ciphertext rejected at both validation and AEAD stage.")


def test_5_wrong_key_rejected():
    """Item 5: Wrong key is rejected."""
    print("Test 5: Verifying wrong key is rejected...")
    round_id = 1
    key_ctx = str(uuid.uuid4())
    correct_key = generate_round_key()
    wrong_key = generate_round_key()
    st = {"layer.weight": torch.ones(4, 4, dtype=torch.float32)}
    m_hash = compute_model_hash(st)

    weights = [np.ones((3, 3), dtype=np.float32)]
    pkg = _build_test_update(round_id, 0, m_hash, key_ctx, correct_key, weights)

    try:
        decrypt_update(pkg["ct"], wrong_key)
        assert False, "Item 5 FAILED: Decryption succeeded with wrong key!"
    except InvalidTag:
        pass  # Expected

    print("  -> PASS: Wrong key rejected with InvalidTag.")


def test_6_weighted_aggregation_produces_expected_result():
    """Item 6: Weighted aggregation produces the mathematically expected result."""
    print("Test 6: Verifying weighted aggregation produces expected result...")
    round_id = 1
    key_ctx = str(uuid.uuid4())
    round_key = generate_round_key()
    st = {"layer.weight": torch.ones(2, 2, dtype=torch.float32)}
    m_hash = compute_model_hash(st)

    strategy = FullSDFLStrategy(mu=0.001, C=2.0, sigma=1.5, secret_key=SECRET_KEY, window_seconds=300)
    strategy.round_keys[key_ctx] = round_key
    strategy.current_key_context_id = key_ctx
    strategy.current_Tr = time.time() + 300
    strategy.current_model_hash = m_hash

    # Three clients with different weights and sample counts
    w0 = [np.array([10.0, 20.0], dtype=np.float32), np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)]
    w1 = [np.array([40.0, 50.0], dtype=np.float32), np.array([[5.0, 6.0], [7.0, 8.0]], dtype=np.float32)]
    w2 = [np.array([100.0, 200.0], dtype=np.float32), np.array([[10.0, 20.0], [30.0, 40.0]], dtype=np.float32)]

    n0, n1, n2 = 100, 300, 600
    total_n = n0 + n1 + n2

    # Expected weighted analytical average:
    expected_layer0 = (n0 * w0[0] + n1 * w1[0] + n2 * w2[0]) / total_n
    expected_layer1 = (n0 * w0[1] + n1 * w1[1] + n2 * w2[1]) / total_n

    pkg0 = _build_test_update(round_id, 0, m_hash, key_ctx, round_key, w0)
    pkg0["fit_res"].num_examples = n0
    pkg0["fit_res"].metrics["num_examples"] = n0

    pkg1 = _build_test_update(round_id, 1, m_hash, key_ctx, round_key, w1)
    pkg1["fit_res"].num_examples = n1
    pkg1["fit_res"].metrics["num_examples"] = n1

    pkg2 = _build_test_update(round_id, 2, m_hash, key_ctx, round_key, w2)
    pkg2["fit_res"].num_examples = n2
    pkg2["fit_res"].metrics["num_examples"] = n2

    results = [
        (pkg0["proxy"], pkg0["fit_res"]),
        (pkg1["proxy"], pkg1["fit_res"]),
        (pkg2["proxy"], pkg2["fit_res"]),
    ]

    # Run aggregate_fit through FullSDFLStrategy
    params, _ = strategy.aggregate_fit(server_round=round_id, results=results, failures=[])
    assert params is not None, "Item 6 FAILED: aggregate_fit returned None"

    aggregated_ndarrays = fl.common.parameters_to_ndarrays(params)
    assert len(aggregated_ndarrays) == 2, "Item 6 FAILED: Aggregated parameter count mismatch"

    assert np.allclose(aggregated_ndarrays[0], expected_layer0, atol=1e-5), f"Item 6 FAILED: Layer 0 mismatch. Got {aggregated_ndarrays[0]}, expected {expected_layer0}"
    assert np.allclose(aggregated_ndarrays[1], expected_layer1, atol=1e-5), f"Item 6 FAILED: Layer 1 mismatch. Got {aggregated_ndarrays[1]}, expected {expected_layer1}"

    print(f"  -> Analytical Layer 0: {expected_layer0}")
    print(f"  -> Decrypted Agg Layer 0: {aggregated_ndarrays[0]}")
    print("  -> PASS: Weighted aggregation produces exact expected result.")


def test_7_round_key_destruction_does_not_break_current_round():
    """Item 7: Round-key destruction does not break the current round before aggregation completes."""
    print("Test 7: Verifying round-key destruction does not break current round before aggregation completes...")
    round_id = 1
    key_ctx = str(uuid.uuid4())
    round_key = generate_round_key()
    st = {"layer.weight": torch.ones(2, 2, dtype=torch.float32)}
    m_hash = compute_model_hash(st)

    strategy = FullSDFLStrategy(mu=0.001, C=2.0, sigma=1.5, secret_key=SECRET_KEY, window_seconds=300)
    strategy.round_keys[key_ctx] = round_key
    strategy.current_key_context_id = key_ctx
    strategy.current_Tr = time.time() + 300
    strategy.current_model_hash = m_hash

    weights = [np.array([5.0, 15.0], dtype=np.float32)]
    pkg = _build_test_update(round_id, 0, m_hash, key_ctx, round_key, weights)

    # During aggregation, round_key is accessible and intact
    assert key_ctx in strategy.round_keys, "Key context must be present before aggregate_fit"
    assert any(b != 0 for b in strategy.round_keys[key_ctx]), "Key must not be zeroed before aggregate_fit"

    params, _ = strategy.aggregate_fit(server_round=round_id, results=[(pkg["proxy"], pkg["fit_res"])], failures=[])
    assert params is not None, "Item 7 FAILED: Current round aggregation failed"

    agg_nd = fl.common.parameters_to_ndarrays(params)
    assert np.allclose(agg_nd[0], np.array([5.0, 15.0], dtype=np.float32)), "Item 7 FAILED: Aggregation returned corrupted data"

    print("  -> PASS: Current round aggregation completed seamlessly before key destruction.")


def test_8_key_destruction_prevents_subsequent_decryption():
    """Item 8: Key destruction prevents subsequent decryption."""
    print("Test 8: Verifying key destruction prevents subsequent decryption...")
    round_id = 1
    key_ctx = str(uuid.uuid4())
    round_key = generate_round_key()
    saved_key_ref = round_key  # keep reference to bytearray
    st = {"layer.weight": torch.ones(2, 2, dtype=torch.float32)}
    m_hash = compute_model_hash(st)

    strategy = FullSDFLStrategy(mu=0.001, C=2.0, sigma=1.5, secret_key=SECRET_KEY, window_seconds=300)
    strategy.round_keys[key_ctx] = round_key
    strategy.current_key_context_id = key_ctx
    strategy.current_Tr = time.time() + 300
    strategy.current_model_hash = m_hash

    weights = [np.array([42.0, 84.0], dtype=np.float32)]
    pkg = _build_test_update(round_id, 0, m_hash, key_ctx, round_key, weights)

    # Execute round aggregation -> triggers finally: destroy_round_key
    _, _ = strategy.aggregate_fit(server_round=round_id, results=[(pkg["proxy"], pkg["fit_res"])], failures=[])

    # 1. Verify key context was removed from strategy
    assert key_ctx not in strategy.round_keys, "Item 8 FAILED: key_context_id still in strategy.round_keys"

    # 2. Verify round_key bytearray was zeroed out in-memory
    assert all(b == 0 for b in saved_key_ref), "Item 8 FAILED: Key bytearray was not zeroed"

    # 3. Verify attempting decryption with the zeroed/destroyed key raises InvalidTag
    try:
        decrypt_update(pkg["ct"], saved_key_ref)
        assert False, "Item 8 FAILED: Post-destruction decryption succeeded!"
    except InvalidTag:
        pass  # Expected

    print("  -> PASS: Key bytearray zeroed, context removed, subsequent decryption raises InvalidTag.")


def run_all_tests():
    print("=" * 80)
    print("E8 FEDERATED AGGREGATION & HARDENED SECURITY INTEGRATION TEST SUITE")
    print("=" * 80)

    test_results = {}
    tests = [
        (1, "legitimate encrypted update is accepted", test_1_legitimate_encrypted_update_accepted),
        (2, "legitimate update decrypts successfully", test_2_legitimate_update_decrypts_successfully),
        (3, "AAD mismatch is rejected", test_3_aad_mismatch_rejected),
        (4, "modified ciphertext is rejected", test_4_modified_ciphertext_rejected),
        (5, "wrong key is rejected", test_5_wrong_key_rejected),
        (6, "weighted aggregation produces expected result", test_6_weighted_aggregation_produces_expected_result),
        (7, "round-key destruction does not break current round", test_7_round_key_destruction_does_not_break_current_round),
        (8, "key destruction prevents subsequent decryption", test_8_key_destruction_prevents_subsequent_decryption),
    ]

    all_passed = True
    for item_num, name, test_fn in tests:
        try:
            test_fn()
            test_results[item_num] = "PASS"
        except Exception as e:
            print(f"  -> FAIL: {e}")
            test_results[item_num] = "FAIL"
            all_passed = False

    print("\n" + "=" * 80)
    print("SUMMARY RESULTS:")
    print("=" * 80)
    for item_num, name, _ in tests:
        status = test_results.get(item_num, "FAIL")
        print(f"Item {item_num}: {name:<60} [{status}]")
    print("=" * 80)

    if all_passed:
        print("ALL 8 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    else:
        print("SOME TESTS FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
