import os
import re
import base64
import pytest
from platform.coordinator.config import get_coordinator_secret

def test_no_hardcoded_keys():
    platform_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # 1. Recursively scan all .py files under platform/
    for root, _, files in os.walk(platform_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                # Skip checking this test file itself, since it contains the search string
                if file == "test_secrets.py":
                    continue
                    
                with open(filepath, "r") as f:
                    content = f.read()
                    
                # Assert none contain the old hardcoded signing key
                assert "sdfl_coordinator_signing_secret_key_32bytes" not in content, f"Hardcoded secret key found in {filepath}"
                
                # Assert none contain raw SECRET_KEY = b"..." assignments
                match = re.search(r"SECRET_KEY\s*=\s*b['\"]", content)
                assert not match, f"Raw SECRET_KEY assignment found in {filepath}"

    # 2. Assert .env files are in .gitignore
    root_dir = os.path.abspath(os.path.join(platform_dir, ".."))
    gitignore_path = os.path.join(root_dir, ".gitignore")
    assert os.path.exists(gitignore_path), ".gitignore does not exist in root directory"
    
    with open(gitignore_path, "r") as f:
        gitignore_content = f.read()
    
    # Check if any variant of .env is ignored
    assert ".env" in gitignore_content or "*.env" in gitignore_content, ".env is not configured in .gitignore"

def test_config_raises_without_env(monkeypatch):
    # Unset COORDINATOR_SECRET env var
    monkeypatch.delenv("COORDINATOR_SECRET", raising=False)
    with pytest.raises(ValueError, match="COORDINATOR_SECRET environment variable missing"):
        get_coordinator_secret()

def test_key_must_be_32_bytes(monkeypatch):
    # Set COORDINATOR_SECRET to base64 of a 16-byte string
    short_key = os.urandom(16)
    short_encoded = base64.b64encode(short_key).decode("utf-8")
    monkeypatch.setenv("COORDINATOR_SECRET", short_encoded)
    with pytest.raises(ValueError, match="COORDINATOR_SECRET must decode to exactly 32 bytes"):
        get_coordinator_secret()
