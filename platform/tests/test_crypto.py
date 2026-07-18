import os
import json
import time
import uuid
import base64

os.environ["COORDINATOR_SECRET"] = base64.b64encode(b"x" * 32).decode()

import pytest
import torch
import numpy as np
from cryptography.exceptions import InvalidTag

from crypto import (
    generate_round_key,
    client_encrypt,
    decrypt_update,
    destroy_round_key,
    create_certificate,
    sign_certificate,
    verify_certificate,
    write_audit_log,
    server_aggregate,
)
from e7_temporal import TemporalCheckpointingSecAgg
from platform.coordinator.config import get_coordinator_secret


class DummyClientProxy:
    def __init__(self, cid):
        self.cid = cid


class DummyFitRes:
    def __init__(self, metrics, num_examples=100):
        self.metrics = metrics
        self.num_examples = num_examples


SDFL_TEST_SECRET = b"test_coordinator_secret_key_32bytes"


def test_timely_submission_accepted():
    round_id = 1
    key_context_id = str(uuid.uuid4())
    expiry_timestamp = time.time() + 10
    cert = create_certificate(
        round_id=round_id, model_hash="dummy", participants=["c0"],
        key_context_id=key_context_id, expiry_timestamp=expiry_timestamp,
    )
    signature = sign_certificate(cert, SDFL_TEST_SECRET)

    strategy = TemporalCheckpointingSecAgg(
        mu=0.001, C=2.0, sigma=1.5, secret_key=SDFL_TEST_SECRET, window_seconds=10
    )
    strategy.current_key_context_id = key_context_id
    strategy.current_Tr = expiry_timestamp

    key = generate_round_key()
    strategy.round_keys[key_context_id] = key
    ct = client_encrypt(torch.ones(10), key)

    fit_res_metrics = {
        "nonce_hex": ct["nonce"].hex(),
        "ciphertext_hex": ct["ciphertext"].hex(),
        "certificate": json.dumps(cert),
        "signature": signature,
        "key_context_id": key_context_id,
    }
    fit_res = DummyFitRes(fit_res_metrics)
    is_valid, reason = strategy.validate_update(fit_res, current_time=expiry_timestamp - 1.0)
    assert is_valid, f"Expected accepted, got: {reason}"


def test_expired_submission_rejected():
    round_id = 1
    key_context_id = str(uuid.uuid4())
    expiry_timestamp = time.time() + 10
    cert = create_certificate(
        round_id=round_id, model_hash="dummy", participants=["c0"],
        key_context_id=key_context_id, expiry_timestamp=expiry_timestamp,
    )
    signature = sign_certificate(cert, SDFL_TEST_SECRET)

    strategy = TemporalCheckpointingSecAgg(
        mu=0.001, C=2.0, sigma=1.5, secret_key=SDFL_TEST_SECRET, window_seconds=10
    )
    strategy.current_key_context_id = key_context_id
    strategy.current_Tr = expiry_timestamp

    key = generate_round_key()
    strategy.round_keys[key_context_id] = key
    ct = client_encrypt(torch.ones(10), key)

    fit_res_metrics = {
        "nonce_hex": ct["nonce"].hex(),
        "ciphertext_hex": ct["ciphertext"].hex(),
        "certificate": json.dumps(cert),
        "signature": signature,
        "key_context_id": key_context_id,
    }
    fit_res = DummyFitRes(fit_res_metrics)
    is_valid, reason = strategy.validate_update(fit_res, current_time=expiry_timestamp + 1.0)
    assert not is_valid
    assert reason == "expired"


def test_context_mismatch_rejected():
    round_id = 1
    key_context_id = str(uuid.uuid4())
    expiry_timestamp = time.time() + 10
    cert = create_certificate(
        round_id=round_id, model_hash="dummy", participants=["c0"],
        key_context_id=key_context_id, expiry_timestamp=expiry_timestamp,
    )
    signature = sign_certificate(cert, SDFL_TEST_SECRET)

    strategy = TemporalCheckpointingSecAgg(
        mu=0.001, C=2.0, sigma=1.5, secret_key=SDFL_TEST_SECRET, window_seconds=10
    )
    strategy.current_key_context_id = key_context_id
    strategy.current_Tr = expiry_timestamp

    key = generate_round_key()
    strategy.round_keys[key_context_id] = key
    ct = client_encrypt(torch.ones(10), key)

    wrong_metrics = {
        "nonce_hex": ct["nonce"].hex(),
        "ciphertext_hex": ct["ciphertext"].hex(),
        "certificate": json.dumps(cert),
        "signature": signature,
        "key_context_id": str(uuid.uuid4()),
    }
    fit_res = DummyFitRes(wrong_metrics)
    is_valid, reason = strategy.validate_update(fit_res, current_time=expiry_timestamp - 1.0)
    assert not is_valid
    assert reason == "mismatch"


def test_post_destruction_raises_invalid_tag():
    key = generate_round_key()
    ct = client_encrypt(torch.randn(10), key)
    destroy_round_key(key)
    with pytest.raises(InvalidTag):
        decrypt_update(ct, key)


def test_audit_log_has_all_3_events():
    audit_path = "test_audit_log_crypto.jsonl"
    if os.path.exists(audit_path):
        os.remove(audit_path)

    class DummyClientManager:
        def sample(self, num_clients, min_num_clients=None):
            return [DummyClientProxy("c0"), DummyClientProxy("c1"), DummyClientProxy("c2")]

        def num_available(self):
            return 3

    from e4_dpsgd import get_parameters
    from model import ResUNetPlusPlus
    from e4_dpsgd import fix_model_for_opacus
    import flwr as fl

    strategy = TemporalCheckpointingSecAgg(
        mu=0.001, C=2.0, sigma=1.5, secret_key=SDFL_TEST_SECRET, window_seconds=10
    )
    strategy.AUDIT_LOG_PATH = audit_path

    test_model = ResUNetPlusPlus()
    fix_model_for_opacus(test_model)
    test_params = fl.common.ndarrays_to_parameters(get_parameters(test_model))

    fit_configs = strategy.configure_fit(1, test_params, DummyClientManager())
    client_config = fit_configs[0][1].config

    round_key_hex = client_config["round_key_hex"]
    round_key = bytearray(bytes.fromhex(round_key_hex))

    fresh_ct = client_encrypt(torch.ones(10), round_key)
    fresh_metrics = {
        "nonce_hex": fresh_ct["nonce"].hex(),
        "ciphertext_hex": fresh_ct["ciphertext"].hex(),
        "certificate": client_config["certificate"],
        "signature": client_config["signature"],
        "key_context_id": client_config["key_context_id"],
    }
    client_proxy = DummyClientProxy("c0")
    strategy.aggregate_fit(1, [(client_proxy, DummyFitRes(fresh_metrics))], [])

    with open(audit_path) as f:
        events = [json.loads(line.strip())["event"] for line in f]

    assert "round_open" in events
    assert "round_close" in events
    assert "key_destroyed" in events

    if os.path.exists(audit_path):
        os.remove(audit_path)


def test_weighted_aggregate_correctness():
    key = generate_round_key()
    w1 = [np.array([1.0, 2.0]), np.array([3.0])]
    w2 = [np.array([4.0, 5.0]), np.array([6.0])]
    w3 = [np.array([7.0, 8.0]), np.array([9.0])]

    ct1 = client_encrypt(w1, key)
    ct2 = client_encrypt(w2, key)
    ct3 = client_encrypt(w3, key)

    num_examples = [100, 200, 300]
    total = sum(num_examples)
    result = server_aggregate([ct1, ct2, ct3], key, num_examples)

    expected_layer0 = (100/total) * w1[0] + (200/total) * w2[0] + (300/total) * w3[0]
    expected_layer1 = (100/total) * w1[1] + (200/total) * w2[1] + (300/total) * w3[1]

    assert np.allclose(result[0], expected_layer0)
    assert np.allclose(result[1], expected_layer1)


def test_32_byte_key_required(monkeypatch):
    short_key = os.urandom(16)
    short_encoded = base64.b64encode(short_key).decode()
    monkeypatch.setenv("COORDINATOR_SECRET", short_encoded)
    with pytest.raises(ValueError, match="COORDINATOR_SECRET must decode to exactly 32 bytes"):
        get_coordinator_secret()
