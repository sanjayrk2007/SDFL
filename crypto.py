import os
import json
import time
import uuid
import hmac
import hashlib
import pickle

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def generate_round_key():
    return AESGCM.generate_key(bit_length=256)

def encrypt_update(weights, round_key):

    aesgcm = AESGCM(round_key)

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

    aesgcm = AESGCM(round_key)

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

def destroy_round_key(round_key):

    del round_key

def write_audit_log(
    filename,
    event
):

    with open(filename, "a") as f:
        f.write(
            json.dumps(event) + "\n"
        )