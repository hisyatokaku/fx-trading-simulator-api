#!/bin/bash
# app/DB VM のブートディスクを拡張する（10GB → config.sh の APPDB_DISK_SIZE）
# Day 2 の colab_template 試行錯誤で balances テーブルが数GB増えるための対策。
# オンライン拡張なので VM 停止は不要。縮小は不可なので注意。
set -euo pipefail
source "$(dirname "$0")/config.sh"

gcloud compute disks resize "$APPDB_BOOT_DISK" \
    --project="$PROJECT" --zone="$ZONE" --size="$APPDB_DISK_SIZE" --quiet

# パーティションとファイルシステムを拡張（Debian 12 / ext4 前提）
gcloud compute ssh "$APPDB_VM" --project="$PROJECT" --zone="$ZONE" --command='
    sudo apt-get install -y cloud-guest-utils >/dev/null 2>&1 || true
    sudo growpart /dev/sda 1 || true   # 既に拡張済みなら失敗してよい
    sudo resize2fs /dev/sda1
    df -h /
'
echo "done: disk resized to $APPDB_DISK_SIZE"
