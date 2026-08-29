#!/bin/bash
# ノートブック（等のファイル）を /etc/skel と全参加者のホームに配布する。
#
# 使い方:
#   bash 07_distribute_notebook.sh document/tutorial.ipynb
#
# - /etc/skel に置くので、配布後に初回ログインした新規ユーザーにも自動で入る
# - 既存ホームには for 文でコピー。既に同名ファイルがある人は必ずスキップする
#   （参加者の編集内容を壊さないため。上書きオプションは事故防止のため意図的に無い）
# - 内容を更新して配り直したいときは別のファイル名にする（例: tutorial-v2.ipynb）
set -euo pipefail
source "$(dirname "$0")/config.sh"

FILE=${1:?usage: bash 07_distribute_notebook.sh <file>}
BASE=$(basename "$FILE")

gcloud compute scp "$FILE" "$TLJH_VM:/tmp/$BASE" --project="$PROJECT" --zone="$ZONE"

gcloud compute ssh "$TLJH_VM" --project="$PROJECT" --zone="$ZONE" --command="
    set -e
    sudo install -m 644 /tmp/$BASE /etc/skel/$BASE
    echo 'placed in /etc/skel (new users will receive it on first login)'
    for h in /home/jupyter-*; do
        [ -d \"\$h\" ] || continue
        u=\$(basename \"\$h\")
        if [ -f \"\$h/$BASE\" ]; then
            echo \"skip    \$u (already has $BASE)\"
            continue
        fi
        sudo cp \"/tmp/$BASE\" \"\$h/$BASE\"
        sudo chown \"\$u:\" \"\$h/$BASE\"
        echo \"copied  \$u\"
    done
    rm -f /tmp/$BASE
"
echo "done: $BASE distributed"
