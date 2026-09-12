import os
import json
import time
import uuid
import hmac
import hashlib
import struct
import io
import numpy as np
import torch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

MAGIC = b"SDFL"
VERSION = 1

TYPE_TORCH_TENSOR = 1
TYPE_NUMPY_NDARRAY = 2
TYPE_LIST_TORCH_TENSOR = 3
TYPE_LIST_NUMPY_NDARRAY = 4

def generate_round_key():
    return bytearray(AESGCM.generate_key(bit_length=256))

def serialize_weights(weights) -> bytes:
    """
    Explicit, deterministic binary serialization for model weights.
    Does NOT use pickle.

    Supported input types:
    - torch.Tensor
    - np.ndarray
    - list or tuple of torch.Tensor
    - list or tuple of np.ndarray
    """
    buffer = io.BytesIO()
    buffer.write(MAGIC)
    buffer.write(struct.pack(">B", VERSION))

    if isinstance(weights, torch.Tensor):
        struct_type = TYPE_TORCH_TENSOR
        items = [weights]
    elif isinstance(weights, np.ndarray):
        struct_type = TYPE_NUMPY_NDARRAY
        items = [weights]
    elif isinstance(weights, (list, tuple)):
        if len(weights) == 0:
            raise ValueError("Cannot serialize empty weights list")
        if isinstance(weights[0], torch.Tensor):
            struct_type = TYPE_LIST_TORCH_TENSOR
            items = list(weights)
        elif isinstance(weights[0], np.ndarray):
            struct_type = TYPE_LIST_NUMPY_NDARRAY
            items = list(weights)
        else:
            raise TypeError(f"Unsupported item type in weights list: {type(weights[0])}")
    else:
        raise TypeError(f"Unsupported weights type for serialization: {type(weights)}")

    buffer.write(struct.pack(">B", struct_type))
    buffer.write(struct.pack(">I", len(items)))

    for item in items:
        if isinstance(item, torch.Tensor):
            arr = item.detach().cpu().numpy()
        elif isinstance(item, np.ndarray):
            arr = item
        else:
            raise TypeError(f"Inconsistent element type in weights list: {type(item)}")

        if not arr.flags['C_CONTIGUOUS']:
            arr = np.ascontiguousarray(arr)

        dtype_str = str(arr.dtype).encode('ascii')
        dtype_len = len(dtype_str)
        if dtype_len > 255:
            raise ValueError("Dtype string too long")

        shape = arr.shape
        ndim = len(shape)

        raw_bytes = arr.tobytes()
        bytes_len = len(raw_bytes)

        buffer.write(struct.pack(">B", dtype_len))
        buffer.write(dtype_str)
        buffer.write(struct.pack(">H", ndim))
        for dim in shape:
            buffer.write(struct.pack(">Q", dim))
        buffer.write(struct.pack(">Q", bytes_len))
        buffer.write(raw_bytes)

    return buffer.getvalue()

def deserialize_weights(payload: bytes):
    """
    Deserializes model weights from explicit binary representation.
    Does NOT use pickle.loads().
    """
    if not isinstance(payload, (bytes, bytearray, memoryview)):
        raise TypeError("Payload must be bytes-like")

    stream = io.BytesIO(payload)

    magic = stream.read(4)
    if magic != MAGIC:
        raise ValueError(f"Invalid magic header: expected {MAGIC!r}, got {magic!r}")

    version_bytes = stream.read(1)
    if len(version_bytes) < 1:
        raise ValueError("Truncated payload: missing version")
    version = struct.unpack(">B", version_bytes)[0]
    if version != VERSION:
        raise ValueError(f"Unsupported payload version: {version}")

    struct_type_bytes = stream.read(1)
    if len(struct_type_bytes) < 1:
        raise ValueError("Truncated payload: missing struct type")
    struct_type = struct.unpack(">B", struct_type_bytes)[0]

    num_items_bytes = stream.read(4)
    if len(num_items_bytes) < 4:
        raise ValueError("Truncated payload: missing num items")
    num_items = struct.unpack(">I", num_items_bytes)[0]

    items = []
    for _ in range(num_items):
        dtype_len_bytes = stream.read(1)
        if len(dtype_len_bytes) < 1:
            raise ValueError("Truncated payload: missing dtype len")
        dtype_len = struct.unpack(">B", dtype_len_bytes)[0]

        dtype_str_bytes = stream.read(dtype_len)
        if len(dtype_str_bytes) < dtype_len:
            raise ValueError("Truncated payload: incomplete dtype str")
        dtype_str = dtype_str_bytes.decode('ascii')

        try:
            dtype = np.dtype(dtype_str)
        except Exception as e:
            raise ValueError(f"Invalid dtype string '{dtype_str}': {e}")

        ndim_bytes = stream.read(2)
        if len(ndim_bytes) < 2:
            raise ValueError("Truncated payload: missing ndim")
        ndim = struct.unpack(">H", ndim_bytes)[0]

        shape = []
        for _ in range(ndim):
            dim_bytes = stream.read(8)
            if len(dim_bytes) < 8:
                raise ValueError("Truncated payload: missing shape dim")
            shape.append(struct.unpack(">Q", dim_bytes)[0])
        shape = tuple(shape)

        bytes_len_bytes = stream.read(8)
        if len(bytes_len_bytes) < 8:
            raise ValueError("Truncated payload: missing bytes len")
        bytes_len = struct.unpack(">Q", bytes_len_bytes)[0]

        raw_bytes = stream.read(bytes_len)
        if len(raw_bytes) < bytes_len:
            raise ValueError("Truncated payload: incomplete data bytes")

        arr = np.frombuffer(raw_bytes, dtype=dtype).reshape(shape).copy()
        items.append(arr)

    if stream.read(1):
        raise ValueError("Payload has trailing unparsed bytes")

    if struct_type == TYPE_TORCH_TENSOR:
        return torch.from_numpy(items[0])
    elif struct_type == TYPE_NUMPY_NDARRAY:
        return items[0]
    elif struct_type == TYPE_LIST_TORCH_TENSOR:
        return [torch.from_numpy(item) for item in items]
    elif struct_type == TYPE_LIST_NUMPY_NDARRAY:
        return items
    else:
        raise ValueError(f"Unknown structure type tag: {struct_type}")

def _format_aad(associated_data):
    if associated_data is None:
        return None
    if isinstance(associated_data, str):
        return associated_data.encode('utf-8')
    if isinstance(associated_data, bytearray):
        return bytes(associated_data)
    if isinstance(associated_data, bytes):
        return associated_data
    raise TypeError(f"Associated data must be bytes, bytearray, str, or None; got {type(associated_data)}")

def encrypt_update(weights, round_key, associated_data=None):
    aesgcm = AESGCM(bytes(round_key))
    nonce = os.urandom(12)
    payload = serialize_weights(weights)
    aad = _format_aad(associated_data)

    ciphertext = aesgcm.encrypt(
        nonce,
        payload,
        aad
    )

    res = {
        "nonce": nonce,
        "ciphertext": ciphertext
    }
    if associated_data is not None:
        res["associated_data"] = associated_data
    return res

def decrypt_update(encrypted_data, round_key, associated_data=None):
    aesgcm = AESGCM(bytes(round_key))
    aad = associated_data
    if aad is None and isinstance(encrypted_data, dict):
        aad = encrypted_data.get("associated_data", encrypted_data.get("aad", None))
    aad = _format_aad(aad)

    payload = aesgcm.decrypt(
        encrypted_data["nonce"],
        encrypted_data["ciphertext"],
        aad
    )

    return deserialize_weights(payload)

def create_certificate(
    round_id,
    model_hash,
    participants,
    key_context_id,
    expiry_timestamp
):
    return {
        "round_id": round_id,
        "model_hash": model_hash,
        "participants": participants,
        "key_context_id": key_context_id,
        "expiry_timestamp": expiry_timestamp
    }

def sign_certificate(certificate, secret_key):
    message = json.dumps(
        certificate,
        sort_keys=True
    ).encode()

    signature = hmac.new(
        secret_key,
        message,
        hashlib.sha256
    ).hexdigest()

    return signature

def verify_certificate(
    certificate,
    signature,
    secret_key
):
    expected = sign_certificate(
        certificate,
        secret_key
    )

    return hmac.compare_digest(
        signature,
        expected
    )

def destroy_round_key(round_key: bytearray):
    for i in range(len(round_key)):
        round_key[i] = 0
    del round_key

def write_audit_log(
    filename,
    event
):
    with open(filename, "a") as f:
        f.write(
            json.dumps(event) + "\n"
        )

def client_encrypt(update_weights, round_key, associated_data=None):
    return encrypt_update(update_weights, round_key, associated_data=associated_data)

def server_aggregate(list_of_ciphertexts, round_key, num_examples_list=None, associated_data=None):
    """
    Aggregates encrypted client model updates.

    If num_examples_list is provided (a list of integers representing sample counts),
    performs a weighted average. If None, falls back to unweighted average.
    """
    decrypted_updates = [decrypt_update(ct, round_key, associated_data=associated_data) for ct in list_of_ciphertexts]

    if isinstance(decrypted_updates[0], torch.Tensor):
        if num_examples_list is not None:
            total = sum(num_examples_list)
            if total == 0:
                total = 1
            stacked = torch.stack(decrypted_updates)
            w = torch.tensor(num_examples_list, dtype=stacked.dtype, device=stacked.device)
            w = w / total
            for _ in range(stacked.dim() - 1):
                w = w.unsqueeze(-1)
            return torch.sum(stacked * w, dim=0)
        else:
            stacked = torch.stack(decrypted_updates)
            return torch.mean(stacked, dim=0)
    elif isinstance(decrypted_updates[0], list) and len(decrypted_updates[0]) > 0 and isinstance(decrypted_updates[0][0], np.ndarray):
        if num_examples_list is not None:
            total = sum(num_examples_list)
            if total == 0:
                total = 1
            aggregated = []
            for layer_idx in range(len(decrypted_updates[0])):
                weighted_sum = sum(
                    (n / total) * update[layer_idx]
                    for n, update in zip(num_examples_list, decrypted_updates)
                )
                aggregated.append(weighted_sum)
            return aggregated
        else:
            num_clients = len(decrypted_updates)
            aggregated = []
            for layer_idx in range(len(decrypted_updates[0])):
                layer_sum = sum(update[layer_idx] for update in decrypted_updates)
                aggregated.append(layer_sum / num_clients)
            return aggregated
    elif isinstance(decrypted_updates[0], list) and len(decrypted_updates[0]) > 0 and isinstance(decrypted_updates[0][0], torch.Tensor):
        if num_examples_list is not None:
            total = sum(num_examples_list)
            if total == 0:
                total = 1
            aggregated = []
            for layer_idx in range(len(decrypted_updates[0])):
                weighted_sum = sum(
                    (n / total) * update[layer_idx]
                    for n, update in zip(num_examples_list, decrypted_updates)
                )
                aggregated.append(weighted_sum)
            return aggregated
        else:
            num_clients = len(decrypted_updates)
            aggregated = []
            for layer_idx in range(len(decrypted_updates[0])):
                layer_sum = sum(update[layer_idx] for update in decrypted_updates)
                aggregated.append(layer_sum / num_clients)
            return aggregated
    elif isinstance(decrypted_updates[0], np.ndarray):
        if num_examples_list is not None:
            total = sum(num_examples_list)
            if total == 0:
                total = 1
            weighted_sum = sum(
                (n / total) * update
                for n, update in zip(num_examples_list, decrypted_updates)
            )
            return weighted_sum
        else:
            num_clients = len(decrypted_updates)
            return sum(decrypted_updates) / num_clients
    else:
        raise TypeError("Unsupported weight type for secure aggregation")

def run_crypto_tests():
    print("=== Running SDFL Crypto Unit Tests ===")

    # A. Serialization round trip
    weights_np = [np.array([1.0, 2.0, 3.0], dtype=np.float32)]
    ser = serialize_weights(weights_np)
    deser = deserialize_weights(ser)
    assert len(deser) == 1 and np.array_equal(deser[0], weights_np[0]), "Test A failed"
    print("Test A passed: Serialization round trip")

    # B. Multiple layers
    layers = [np.random.randn(10, 5).astype(np.float32), np.random.randn(5).astype(np.float32)]
    ser_b = serialize_weights(layers)
    deser_b = deserialize_weights(ser_b)
    assert len(deser_b) == 2 and all(np.array_equal(d, l) for d, l in zip(deser_b, layers)), "Test B failed"
    print("Test B passed: Multiple layers")

    # C. Dtype preservation
    dtypes = [np.float16, np.float32, np.float64, np.int32, np.int64]
    for dt in dtypes:
        w_dt = [np.ones((2, 2), dtype=dt)]
        deser_dt = deserialize_weights(serialize_weights(w_dt))
        assert deser_dt[0].dtype == dt, f"Test C failed for {dt}"
    print("Test C passed: Dtype preservation (float16, float32, float64, int32, int64)")

    # D. Shape preservation
    shapes = [(10,), (5, 4), (2, 3, 4, 5)]
    w_shapes = [np.zeros(s, dtype=np.float32) for s in shapes]
    deser_s = deserialize_weights(serialize_weights(w_shapes))
    assert [d.shape for d in deser_s] == shapes, "Test D failed"
    print("Test D passed: Shape preservation")

    # E. Numerical value preservation
    w_vals = [np.array([-1e5, 0.0, 1e-5, 3.1415926535], dtype=np.float64)]
    deser_v = deserialize_weights(serialize_weights(w_vals))
    assert np.allclose(deser_v[0], w_vals[0]), "Test E failed"
    print("Test E passed: Numerical value preservation")

    # F. Deterministic serialization
    w_det = [np.arange(100, dtype=np.float32).reshape(10, 10)]
    ser1 = serialize_weights(w_det)
    ser2 = serialize_weights(w_det)
    assert ser1 == ser2, "Test F failed"
    print("Test F passed: Deterministic serialization")

    # G. Encrypt/decrypt success
    key = generate_round_key()
    ct = encrypt_update(w_det, key)
    dec = decrypt_update(ct, key)
    assert np.array_equal(dec[0], w_det[0]), "Test G failed"
    print("Test G passed: Encrypt/decrypt success")

    # H. Wrong-key rejection
    wrong_key = generate_round_key()
    try:
        decrypt_update(ct, wrong_key)
        assert False, "Test H failed: Decryption should fail with wrong key"
    except InvalidTag:
        print("Test H passed: Wrong-key rejection (InvalidTag)")

    # I. Modified ciphertext rejection
    mod_ct = dict(ct)
    ct_bytes = bytearray(mod_ct["ciphertext"])
    ct_bytes[0] ^= 0xFF
    mod_ct["ciphertext"] = bytes(ct_bytes)
    try:
        decrypt_update(mod_ct, key)
        assert False, "Test I failed: Decryption should fail with modified ciphertext"
    except InvalidTag:
        print("Test I passed: Modified ciphertext rejection (InvalidTag)")

    # J. Modified nonce rejection
    mod_nonce = dict(ct)
    n_bytes = bytearray(mod_nonce["nonce"])
    n_bytes[0] ^= 0xFF
    mod_nonce["nonce"] = bytes(n_bytes)
    try:
        decrypt_update(mod_nonce, key)
        assert False, "Test J failed: Decryption should fail with modified nonce"
    except InvalidTag:
        print("Test J passed: Modified nonce rejection (InvalidTag)")

    # K. Modified AAD rejection
    ct_aad = encrypt_update(w_det, key, associated_data="round-1-cert")
    try:
        decrypt_update(ct_aad, key, associated_data="round-2-cert")
        assert False, "Test K failed: Decryption should fail with modified AAD"
    except InvalidTag:
        print("Test K passed: Modified AAD rejection (InvalidTag)")

    # L. Invalid serialized payload rejection
    fake_payload = b"SDFL\x01\x01\x00\x00\x00\x01\x07float32\x00\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x10TRUNCATED"
    valid_key = generate_round_key()
    fake_ct = encrypt_update(w_det, valid_key)
    # Tamper payload bytes inside valid AESGCM payload to trigger deserialization error or tag mismatch
    try:
        deserialize_weights(fake_payload)
        assert False, "Test L failed: Should fail deserializing invalid payload"
    except (ValueError, TypeError, struct.error):
        print("Test L passed: Invalid serialized payload rejection")

    # M. Weighted aggregation compatibility
    client1_w = [np.array([10.0, 20.0], dtype=np.float32)]
    client2_w = [np.array([30.0, 40.0], dtype=np.float32)]
    ct1 = encrypt_update(client1_w, key)
    ct2 = encrypt_update(client2_w, key)

    # Weighted 1:3 ratio -> (1*10 + 3*30)/4 = 100/4 = 25, (1*20 + 3*40)/4 = 140/4 = 35
    agg = server_aggregate([ct1, ct2], key, num_examples_list=[100, 300])
    assert np.allclose(agg[0], np.array([25.0, 35.0], dtype=np.float32)), f"Test M failed: got {agg[0]}"
    print("Test M passed: Weighted aggregation compatibility")

    # N. Key destruction zeroes bytearray
    key_to_destroy = generate_round_key()
    assert any(b != 0 for b in key_to_destroy), "Key should not be all zeroes initially"
    destroy_round_key(key_to_destroy)
    assert all(b == 0 for b in key_to_destroy), "Test N failed: Key bytearray was not zeroed"
    print("Test N passed: Key destruction zeroes bytearray")

    print("\nAll 14 crypto unit tests passed successfully!\n")

if __name__ == "__main__":
    run_crypto_tests()
