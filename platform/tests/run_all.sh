#!/bin/bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHON="${ROOT_DIR}/.venv/bin/python"

echo "=== SDFL Platform Test Suite ==="
echo ""

echo "Phase 1: Syntax checks"
$PYTHON -m py_compile platform/tests/test_sanitize.py
$PYTHON -m py_compile platform/tests/test_crypto.py
$PYTHON -m py_compile platform/tests/test_secrets.py
$PYTHON -m py_compile platform/tests/test_late_submission.py
$PYTHON -m py_compile platform/tests/test_sybil.py
$PYTHON -m py_compile platform/tests/test_key_destruction.py
$PYTHON -m py_compile platform/tests/test_e2e_round.py
$PYTHON -m py_compile platform/tests/test_rollback.py
echo "All Python files compile cleanly"
echo ""

echo "Phase 2: Secret scan"
MATCHES=$(find platform/ -name "*.py" -not -name "test_secrets.py" -exec grep -l "sdfl_coordinator_signing_secret_key" {} + || true)
if [ -n "$MATCHES" ]; then
    echo "FAIL: Hardcoded secret found in $MATCHES"
    exit 1
fi
echo "No hardcoded secrets found"
echo ""

echo "Phase 3: Unit tests"
$PYTHON -m pytest platform/tests/test_sanitize.py -v --tb=short
$PYTHON -m pytest platform/tests/test_crypto.py -v --tb=short
$PYTHON -m pytest platform/tests/test_secrets.py -v --tb=short
$PYTHON -m pytest platform/tests/test_key_destruction.py -v --tb=short
$PYTHON -m pytest platform/tests/test_late_submission.py -v --tb=short
echo ""

echo "Phase 4: Integration tests"
$PYTHON -m pytest platform/tests/test_phi_gate.py -v --tb=short
$PYTHON -m pytest platform/tests/test_e2e_round.py -v --tb=short
$PYTHON -m pytest platform/tests/test_rollback.py -v --tb=short
echo ""

if command -v docker &>/dev/null; then
    echo "Phase 5: Docker build check"
    docker build -t sdfl-coordinator -f platform/infra/coordinator/Dockerfile . 2>&1 | tail -5
    docker build -t sdfl-client -f platform/infra/client/Dockerfile . 2>&1 | tail -5
    echo ""
else
    echo "Phase 5: Docker build check (skipped — docker not available)"
fi

echo "=== ALL TESTS PASSED — TRL-4 Platform Ready ==="
