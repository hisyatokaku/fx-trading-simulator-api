#!/bin/bash
# 構築後の検証。API の疎通と、TLJH VM → app VM のレイテンシを確認する
set -euo pipefail
source "$(dirname "$0")/config.sh"

APP_IP=$(gcloud compute instances describe "$APPDB_VM" \
    --project="$PROJECT" --zone="$ZONE" \
    --format='value(networkInterfaces[0].networkIP)')

echo "=== TLJH VM -> app VM ==="
gcloud compute ssh "$TLJH_VM" --project="$PROJECT" --zone="$ZONE" --command="
    set -e
    echo '--- ping (RTT 0.5ms 以下が目安) ---'
    ping -c 5 -q $APP_IP
    echo '--- API health ---'
    curl -sf http://$APP_IP:8000/health && echo ' OK'
    echo '--- /next 100往復の実測 (Day1想定: 1000往復で15〜30秒 = 100往復で1.5〜3秒) ---'
    /opt/tljh/user/bin/python3 - <<'PYEOF'
import requests, time
base = 'http://$APP_IP:8000'
s = requests.Session()
r = s.post(f'{base}/api/trade/start/TEST0/latency-check'); r.raise_for_status()
sid = r.json()['id']
t0 = time.time()
for _ in range(100):
    s.post(f'{base}/api/trade/next', json={'session_id': sid, 'exchange_requests': []}).raise_for_status()
dt = time.time() - t0
print(f'100 steps: {dt:.2f}s ({dt*10:.1f}ms/step)')
PYEOF
"
echo "=== verify done ==="
