#!/bin/bash
# balances テーブルを空にする（Day 1 → Day 2 の間に実行する運用タスク）。
# Day 2 は colab_template 由来の試行錯誤で balances が1日数千万行規模で増えるため、
# 事前に掃除してディスクとクエリ性能を確保する。
#
# 注意: 全ユーザーの全セッション履歴が消える。Day 1 の成績集計が終わってから実行すること。
set -euo pipefail
source "$(dirname "$0")/config.sh"

read -r -p "balances テーブルを TRUNCATE します（全セッション履歴が消えます）。yes で続行: " ans
[ "$ans" = "yes" ] || { echo "aborted"; exit 1; }

gcloud compute ssh "$APPDB_VM" --project="$PROJECT" --zone="$ZONE" --command="
    cd $COMPOSE_DIR
    sudo docker compose exec -T db psql -U fxtrade -c 'TRUNCATE balances;'
    sudo docker compose exec -T db psql -U fxtrade -c 'VACUUM;'
"
echo "done: balances truncated"
