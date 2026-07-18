import json
import time
import uuid

from e7_temporal import TemporalCheckpointingSecAgg
from crypto import generate_round_key, client_encrypt


class DummyClientProxy:
    def __init__(self, cid):
        self.cid = cid


class DummyFitRes:
    def __init__(self, metrics, num_examples=100):
        self.metrics = metrics
        self.num_examples = num_examples


SDFL_TEST_SECRET = b"test_coordinator_secret_key_32bytes"


def test_update_after_Tr_rejected():
    key_context_id = str(uuid.uuid4())
    Tr = time.time() + 2.0

    strategy = TemporalCheckpointingSecAgg(
        mu=0.001, C=2.0, sigma=1.5,
        secret_key=SDFL_TEST_SECRET,
        window_seconds=2,
    )
    strategy.current_key_context_id = key_context_id
    strategy.current_Tr = Tr

    key = generate_round_key()
    strategy.round_keys[key_context_id] = key

    from e7_temporal import create_certificate, sign_certificate
    cert = create_certificate(
        round_id=1, model_hash="dummy",
        participants=["c0"],
        key_context_id=key_context_id,
        expiry_timestamp=Tr,
    )
    signature = sign_certificate(cert, SDFL_TEST_SECRET)

    ct = client_encrypt([0.0], key)

    fit_res_metrics = {
        "nonce_hex": ct["nonce"].hex(),
        "ciphertext_hex": ct["ciphertext"].hex(),
        "certificate": json.dumps(cert),
        "signature": signature,
        "key_context_id": key_context_id,
    }
    fit_res = DummyFitRes(fit_res_metrics)

    is_valid, reason = strategy.validate_update(fit_res, current_time=Tr + 1.0)
    assert is_valid is False
    assert reason == "expired"
