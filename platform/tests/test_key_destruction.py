import torch
import pytest
from cryptography.exceptions import InvalidTag

from crypto import generate_round_key, client_encrypt, decrypt_update, destroy_round_key


def test_key_zeroed_after_destroy():
    key = generate_round_key()
    original = bytes(key)
    assert len(key) == 32
    ct = client_encrypt(torch.randn(10), key)
    destroy_round_key(key)
    assert all(b == 0 for b in key)


def test_decrypt_after_destroy_raises():
    key = generate_round_key()
    ct = client_encrypt(torch.randn(10), key)
    destroy_round_key(key)
    with pytest.raises(InvalidTag):
        decrypt_update(ct, key)


def test_encrypt_then_decrypt_success():
    key = generate_round_key()
    data = torch.tensor([1.0, 2.0, 3.0])
    ct = client_encrypt(data, key)
    result = decrypt_update(ct, key)
    assert torch.allclose(result, data)
