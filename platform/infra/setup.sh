#!/bin/bash
set -euo pipefail

echo "=== SDFL Hospital Node Setup ==="

# 1. Check dependencies
for cmd in docker openssl curl python3; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "Error: $cmd is required but not installed."; exit 1; }
done

# 2. Prompt for coordinator URL and setup token
read -p "Enter coordinator URL (e.g. https://coordinator.sdfl-vendor.com): " COORDINATOR_URL
read -p "Enter one-time setup token (from coordinator admin): " SETUP_TOKEN

# 3. Create certs directory
mkdir -p platform/infra/certs

# 4. Generate client private key and CSR
openssl genrsa -out platform/infra/certs/client.key 2048
openssl req -new \
    -key platform/infra/certs/client.key \
    -subj "/CN=sdfl-hospital-client/O=Hospital/C=IN" \
    -out platform/infra/certs/client.csr

# 5. Send CSR to coordinator for signing
export SDFL_HOSTNAME="$(hostname)"
export SDFL_COORD_URL="${COORDINATOR_URL}"
export SDFL_SETUP_TOKEN="${SETUP_TOKEN}"

RESPONSE=$(python3 -c "
import json, os, sys

with open('platform/infra/certs/client.csr') as f:
    csr_pem = f.read()

payload = json.dumps({
    'hospital_name': os.environ['SDFL_HOSTNAME'],
    'csr_pem': csr_pem,
    'setup_token': os.environ['SDFL_SETUP_TOKEN'],
})

print(payload)
" | curl -s -X POST "${COORDINATOR_URL}/clients/register" \
    -H "Content-Type: application/json" \
    -d @-)

unset SDFL_HOSTNAME SDFL_COORD_URL SDFL_SETUP_TOKEN

# 6. Check for errors
if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if 'hospital_id' in d else 1)" 2>/dev/null; then
    export SDFL_COORD_URL="${COORDINATOR_URL}"

    python3 -c "
import json, os, sys

data = json.load(sys.stdin)

with open('platform/infra/certs/client.crt', 'w') as f:
    f.write(data['client_certificate_pem'])
with open('platform/infra/certs/ca.crt', 'w') as f:
    f.write(data['ca_certificate_pem'])

url = os.environ['SDFL_COORD_URL']
for prefix in ['https://', 'http://']:
    if url.startswith(prefix):
        url = url[len(prefix):]
        break

env_lines = [
    'CLIENT_ID=' + str(data['hospital_id']),
    'COORDINATOR_URL=' + os.environ['SDFL_COORD_URL'],
    'FLOWER_SERVER_ADDRESS=' + url.split('/')[0] + ':8080',
    'SSL_CA_CERT_PATH=/certs/ca.crt',
    'SSL_CLIENT_CERT_PATH=/certs/client.crt',
    'SSL_CLIENT_KEY_PATH=/certs/client.key',
    'EPSILON_KILL_THRESHOLD=3.0',
    'LOCAL_INCOMING_DIR=/data/incoming',
    'LOCAL_DB_PATH=/data/client.db',
]

with open('platform/client/.env', 'w') as f:
    f.write('\n'.join(env_lines) + '\n')

print(data['hospital_id'])
" > /tmp/sdfl_hospital_id.txt

    unset SDFL_COORD_URL
    HOSPITAL_ID=$(cat /tmp/sdfl_hospital_id.txt)
    rm -f /tmp/sdfl_hospital_id.txt

    # 7. Start hospital stack
    docker compose -f platform/infra/docker-compose.client.yml up -d

    echo ""
    echo "=== Hospital node setup complete ==="
    echo "Hospital ID: ${HOSPITAL_ID}"
    echo "Dashboard:   http://localhost:8501"
else
    echo ""
    echo "=== Registration failed ==="
    echo "Response from coordinator:"
    echo "$RESPONSE"
    exit 1
fi
