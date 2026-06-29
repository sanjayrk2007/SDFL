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

def server_aggregate(list_of_ciphertexts, round_key):
    import torch
    import numpy as np

    decrypted_updates = [decrypt_update(ct, round_key) for ct in list_of_ciphertexts]

    if isinstance(decrypted_updates[0], torch.Tensor):
        stacked = torch.stack(decrypted_updates)
        return torch.mean(stacked, dim=0)
    elif isinstance(decrypted_updates[0], list) and len(decrypted_updates[0]) > 0 and isinstance(decrypted_updates[0][0], np.ndarray):
        num_clients = len(decrypted_updates)
        aggregated = []
        for layer_idx in range(len(decrypted_updates[0])):
            layer_sum = sum(update[layer_idx] for update in decrypted_updates)
            aggregated.append(layer_sum / num_clients)
        return aggregated
    else:
        raise TypeError("Unsupported weight type for secure aggregation")
