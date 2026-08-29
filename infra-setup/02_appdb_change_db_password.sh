#!/bin/bash
# Postgres のパスワードを初期値 (fxtrade) から変更する。
# TLJH 参加者は内部ネットワークから 5432 に到達できるため、イベント前に必須。
#
# 使い方: bash 02_appdb_change_db_password.sh <新パスワード>
#
# やること:
#   1. DB 内のユーザーパスワードを ALTER USER で変更
#   2. docker-compose.yml に直書きされている接続情報を新パスワードに書き換え
#      （このリポジトリの compose は .env 参照ではなく environment 直書き方式。
#       接続URL内のパスワードは URL エンコードして埋め込む）
#   3. app コンテナのみ再作成して反映（db コンテナは無停止。ALTER USER は即時有効）
set -euo pipefail
source "$(dirname "$0")/config.sh"

NEW_PASSWORD=${1:?usage: bash 02_appdb_change_db_password.sh <new-password>}

# URL 用エンコード（@ や & 等を含むパスワードでも接続文字列が壊れないように）
ENC_PASSWORD=$(python3 -c 'import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1], safe=""))' "$NEW_PASSWORD")
# sed の置換文字列では & が「マッチ全体」を意味するためエスケープ
SED_RAW=${NEW_PASSWORD//&/\\&}
SED_ENC=${ENC_PASSWORD//&/\\&}

gcloud compute ssh "$APPDB_VM" --project="$PROJECT" --zone="$ZONE" --command="
    set -e
    # ky2001 のホーム配下のため cd はできない。sudo + --project-directory で操作する
    sudo docker compose --project-directory $COMPOSE_DIR exec -T db psql -U fxtrade -c \"ALTER USER fxtrade WITH PASSWORD '$NEW_PASSWORD';\"
    sudo cp $COMPOSE_DIR/docker-compose.yml $COMPOSE_DIR/docker-compose.yml.bak
    sudo sed -i 's|fxtrade:fxtrade@db|fxtrade:$SED_ENC@db|g; s|POSTGRES_PASSWORD: fxtrade|POSTGRES_PASSWORD: $SED_RAW|' $COMPOSE_DIR/docker-compose.yml
    sudo docker compose --project-directory $COMPOSE_DIR up -d --no-deps app
    sleep 5
    curl -sf http://localhost:8000/health && echo ' -> app OK'
"
echo "done: DB password changed and app restarted"
