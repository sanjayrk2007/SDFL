import os
import json
import time
import uuid
import hmac
import hashlib
import pickle

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def generate_round_key():
    return bytearray(AESGCM.generate_key(bit_length=256))

# SECURITY NOTE: Uses pickle for serialization.
# pickle.loads is vulnerable to arbitrary code execution
# if the ciphertext is tampered with and the key is compromised.
# For production use, replace with numpy-based serialization.
def encrypt_update(weights, round_key):

    aesgcm = AESGCM(bytes(round_key))

    nonce = os.urandom(12)

    payload = pickle.dumps(weights)

    ciphertext = aesgcm.encrypt(
        nonce,
        payload,
        None
    )

    return {
        "nonce": nonce,
        "ciphertext": ciphertext
    }

# SECURITY NOTE: Uses pickle for serialization.
# pickle.loads is vulnerable to arbitrary code execution
# if the ciphertext is tampered with and the key is compromised.
# For production use, replace with numpy-based serialization.
def decrypt_update(encrypted_data, round_key):

    aesgcm = AESGCM(bytes(round_key))

    payload = aesgcm.decrypt(
        encrypted_data["nonce"],
        encrypted_data["ciphertext"],
        None
    )

    return pickle.loads(payload)

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

def client_encrypt(update_weights, round_key):
    return encrypt_update(update_weights, round_key)

def server_aggregate(list_of_ciphertexts, round_key, num_examples_list=None):
    """
    Aggregates encrypted client model updates.
    
    If num_examples_list is provided (a list of integers representing sample counts),
    performs a weighted average. If None, falls back to unweighted average.
    """
    import torch
    import numpy as np

    decrypted_updates = [decrypt_update(ct, round_key) for ct in list_of_ciphertexts]

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
    else:
        raise TypeError("Unsupported weight type for secure aggregation")
