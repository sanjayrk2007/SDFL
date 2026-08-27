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

def serialize_weights(weights):
    import struct
    import numpy as np
    import torch
    
    is_tensor = False
    if isinstance(weights, torch.Tensor):
        is_tensor = True
        weights_list = [weights.cpu().numpy()]
    else:
        weights_list = weights
        
    bio = bytearray()
    bio.extend(struct.pack("!?", is_tensor))
    bio.extend(struct.pack("!I", len(weights_list)))
    
    for arr in weights_list:
        if not isinstance(arr, np.ndarray):
            arr = np.array(arr)
        shape = arr.shape
        bio.extend(struct.pack("!I", len(shape)))
        for dim in shape:
            bio.extend(struct.pack("!I", dim))
        dtype_name = arr.dtype.name.encode('utf-8')
        bio.extend(struct.pack("!I", len(dtype_name)))
        bio.extend(dtype_name)
        raw_data = arr.tobytes()
        bio.extend(struct.pack("!I", len(raw_data)))
        bio.extend(raw_data)
        
    return bytes(bio)

def deserialize_weights(serialized_bytes):
    import struct
    import numpy as np
    import torch
    
    offset = 0
    is_tensor, = struct.unpack_from("!?", serialized_bytes, offset)
    offset += 1
    
    num_arrays, = struct.unpack_from("!I", serialized_bytes, offset)
    offset += 4
    
    arrays = []
    for _ in range(num_arrays):
        shape_len, = struct.unpack_from("!I", serialized_bytes, offset)
        offset += 4
        shape = []
        for _ in range(shape_len):
            dim, = struct.unpack_from("!I", serialized_bytes, offset)
            offset += 4
            shape.append(dim)
        shape = tuple(shape)
        
        dtype_len, = struct.unpack_from("!I", serialized_bytes, offset)
        offset += 4
        dtype_name = serialized_bytes[offset:offset+dtype_len].decode('utf-8')
        offset += dtype_len
        
        data_len, = struct.unpack_from("!I", serialized_bytes, offset)
        offset += 4
        raw_data = serialized_bytes[offset:offset+data_len]
        offset += data_len
        
        arr = np.frombuffer(raw_data, dtype=np.dtype(dtype_name)).copy()
        if shape:
            arr = arr.reshape(shape)
        arrays.append(arr)
        
    if is_tensor:
        return torch.from_numpy(arrays[0])
    return arrays

def encrypt_update(weights, round_key, aad=None):
    aesgcm = AESGCM(bytes(round_key))
    nonce = os.urandom(12)
    payload = serialize_weights(weights)
    ciphertext = aesgcm.encrypt(nonce, payload, aad)
    return {
        "nonce": nonce,
        "ciphertext": ciphertext
    }

def decrypt_update(encrypted_data, round_key, aad=None):
    aesgcm = AESGCM(bytes(round_key))
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

def client_encrypt(update_weights, round_key, aad=None):
    return encrypt_update(update_weights, round_key, aad)

def server_aggregate(list_of_ciphertexts, round_key, num_examples_list=None, aad_list=None):
    """
    Aggregates encrypted client model updates.
    
    If num_examples_list is provided (a list of integers representing sample counts),
    performs a weighted average. If None, falls back to unweighted average.
    """
    import torch
    import numpy as np

    decrypted_updates = []
    for i, ct in enumerate(list_of_ciphertexts):
        aad = aad_list[i] if aad_list is not None else None
        decrypted_updates.append(decrypt_update(ct, round_key, aad))

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
