#!/bin/bash
# 共通設定。各スクリプトが source して使う
# shellcheck disable=SC2034

PROJECT=fx-itnern           # kinetic-dream-319407 は絶対に使わない
ZONE=asia-northeast1-b      # 全VMを同一ゾーンに置く（VM間RTT 0.1〜0.5ms）

# --- app/DB VM（既存） ---
APPDB_VM=fx-trade-api-ssd
APPDB_BOOT_DISK=fx-trade-api-ssd-2   # ブートディスク名（gcloud compute disks list で確認済み）
APPDB_DISK_SIZE=30GB                 # 拡張後のサイズ（Day2 で balances が数GB増えるため）
COMPOSE_DIR=/home/ky2001/fxtrade-api # docker compose 一式の場所

# --- TLJH VM（新設） ---
TLJH_VM=fx-tljh
TLJH_MACHINE_TYPE=e2-highmem-8       # 8 vCPU / 64GB。50人×limits.memory 1GB=50GB でもホストOOMが起きない
TLJH_ADMIN_USERS="tonkou kein"       # 管理者（スペース区切り）。Jupyterターミナルからsudo可＝実質root
# pd-balanced は SSD_TOTAL_GB クォータ（500GB）に算入される。Colab ランタイム（約400GB占有）は削除済み（2026-08-29）
# 128GB は 50人×クォータ2GB を使い切っても収まるサイズ（月 $17 程度）
TLJH_BOOT_DISK_SIZE=128GB
TLJH_BOOT_DISK_TYPE=pd-balanced
TLJH_USER_DISK_QUOTA_KB=2097152      # 参加者1人あたりのディスク上限（2GB、KB単位）
TLJH_ADDRESS=fx-tljh-ip              # 静的外部IPの予約名（停止→起動やマシンタイプ変更でURLが変わらないように）
