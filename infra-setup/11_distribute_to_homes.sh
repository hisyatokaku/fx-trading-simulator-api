#!/bin/bash
# 既にログイン済みの参加者のホームに、指定したファイル or ディレクトリを配る。
#
# 07_distribute_notebook.sh との違い:
#   - 07 は「単一ファイルを /etc/skel + 全ホーム」に配る（skel も触る）
#   - 11 は「ファイル or ディレクトリを既存ホームだけ」に配る（skel は触らない）
#     → ディレクトリ（day1/ 等）を配りたい、対象を絞りたいときに使う
#   （新規ログイン者への配布は skel。10_place_in_skel.sh を使う）
#
# 使い方: bash infra-setup/11_distribute_to_homes.sh <ローカルのパス> [ユーザーglob]
#   例:    bash infra-setup/11_distribute_to_homes.sh document/day1
#          → 全ホーム（jupyter-*）に day1/ を配る
#   例:    bash infra-setup/11_distribute_to_homes.sh document/day1 'jupyter-tester-*'
#          → tester のホームだけに配る
#
# 既に同名がある人はスキップする（編集内容を壊さない。冪等）。
set -euo pipefail
source "$(dirname "$0")/config.sh"

SRC=${1:?usage: bash 11_distribute_to_homes.sh <path> [user-glob]}
GLOB=${2:-jupyter-*}
[ -e "$SRC" ] || { echo "not found: $SRC"; exit 1; }
BASE=$(basename "$SRC")

PARENT=$(cd "$(dirname "$SRC")" && pwd)
PAYLOAD=$(mktemp -t home_payload.XXXXXX).tgz
COPYFILE_DISABLE=1 tar -czf "$PAYLOAD" -C "$PARENT" "$BASE"

gcloud compute scp "$PAYLOAD" "$TLJH_VM:/tmp/home_payload.tgz" --project="$PROJECT" --zone="$ZONE" --quiet

gcloud compute ssh "$TLJH_VM" --project="$PROJECT" --zone="$ZONE" --quiet --command="
    set -e
    tmp=\$(mktemp -d)
    tar -xzf /tmp/home_payload.tgz -C \"\$tmp\"
    sudo find \"\$tmp/$BASE\" -name '._*' -delete 2>/dev/null || true
    copied=0; skipped=0
    for h in /home/$GLOB; do
        [ -d \"\$h\" ] || continue
        u=\$(basename \"\$h\")
        if sudo test -e \"\$h/$BASE\"; then
            echo \"skip    \$u (already has $BASE)\"; skipped=\$((skipped+1)); continue
        fi
        sudo cp -r \"\$tmp/$BASE\" \"\$h/$BASE\"
        sudo chown -R \"\${u}:\${u}\" \"\$h/$BASE\"
        echo \"copied  \$u\"; copied=\$((copied+1))
    done
    rm -rf \"\$tmp\" /tmp/home_payload.tgz
    echo \"done: copied \$copied, skipped \$skipped\"
"
echo "done: $BASE を既存ホーム（$GLOB）に配布"
