#!/bin/bash
# TLJH（The Littlest JupyterHub）用 VM を作成する。
# 参加者50人がブラウザからログインしてノートブックを実行する環境。
# プロビジョニングの実体は 04_tljh_provision.sh（startup-script として自動実行される）。
#
# 完了後 http://<外部IP> にアクセス。初回ログインは管理者ユーザー名 + 任意のパスワード
# （FirstUseAuthenticator: 初回に入力したパスワードがそのまま登録される）
set -euo pipefail
source "$(dirname "$0")/config.sh"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

# app VM の内部IPを取得（ノートブックからの BASE_URL になる）
APP_IP=$(gcloud compute instances describe "$APPDB_VM" \
    --project="$PROJECT" --zone="$ZONE" \
    --format='value(networkInterfaces[0].networkIP)')
echo "app VM internal IP: $APP_IP"

# 参加者ブラウザ用に HTTP(80) を開放（既にあればスキップ）
if ! gcloud compute firewall-rules describe allow-tljh-http --project="$PROJECT" >/dev/null 2>&1; then
    gcloud compute firewall-rules create allow-tljh-http \
        --project="$PROJECT" \
        --direction=INGRESS --action=ALLOW --rules=tcp:80 \
        --target-tags=tljh
fi

# 静的外部IPを予約（既にあればスキップ）。停止→起動でURLが変わらないようにする
REGION=${ZONE%-*}
if ! gcloud compute addresses describe "$TLJH_ADDRESS" --project="$PROJECT" --region="$REGION" >/dev/null 2>&1; then
    gcloud compute addresses create "$TLJH_ADDRESS" --project="$PROJECT" --region="$REGION"
fi
STATIC_IP=$(gcloud compute addresses describe "$TLJH_ADDRESS" \
    --project="$PROJECT" --region="$REGION" --format='value(address)')
echo "TLJH static IP: $STATIC_IP"

gcloud compute instances create "$TLJH_VM" \
    --project="$PROJECT" --zone="$ZONE" \
    --machine-type="$TLJH_MACHINE_TYPE" \
    --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud \
    --boot-disk-size="$TLJH_BOOT_DISK_SIZE" --boot-disk-type="$TLJH_BOOT_DISK_TYPE" \
    --address="$STATIC_IP" \
    --tags=tljh \
    --metadata=fx-api-internal-ip="$APP_IP",tljh-admin-users="$TLJH_ADMIN_USERS",tljh-user-quota-kb="$TLJH_USER_DISK_QUOTA_KB" \
    --metadata-from-file=startup-script="$SCRIPT_DIR/04_tljh_provision.sh"

cat <<EOF

VM created: $TLJH_VM ($ZONE)
  TLJH URL (プロビジョニング完了後、5〜10分): http://$STATIC_IP  ※静的IPなので停止→起動でも変わらない
  進捗確認: gcloud compute ssh $TLJH_VM --project=$PROJECT --zone=$ZONE \\
              --command='sudo journalctl -u google-startup-scripts -f'
  完了判定: 同 --command='sudo test -f /opt/tljh-provisioned && echo done'
EOF
