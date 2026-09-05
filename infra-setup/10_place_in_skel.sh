#!/bin/bash
# 教材（ファイル or ディレクトリ）を TLJH の /etc/skel に置く。
# /etc/skel の中身は「新規ユーザーの初回ログインでホームが作られる瞬間」にコピーされる。
# = これから初回ログインする参加者（未ログインの人）に配る雛形。
#
# 07_distribute_notebook.sh との違い:
#   - 07 は「単一ファイルを /etc/skel + 既にログイン済みの全ホーム」に配る
#   - 10 は「ファイル or ディレクトリを /etc/skel だけ」に置く（既存ホームには触れない）
#     → day1/ のようにディレクトリごと配りたいとき、未ログイン者だけに配りたいときに使う
#
# 使い方: bash infra-setup/10_place_in_skel.sh <ローカルのパス>
#   例:    bash infra-setup/10_place_in_skel.sh document/day1
#          bash infra-setup/10_place_in_skel.sh document/day2/day2.ipynb
#
# 既に同名が /etc/skel にある場合は中断する（誤上書き防止）。置き換えたいときは
# 先に運営が手動で消してから再実行するか、別名にする。
set -euo pipefail
source "$(dirname "$0")/config.sh"

SRC=${1:?usage: bash 10_place_in_skel.sh <path>}
[ -e "$SRC" ] || { echo "not found: $SRC"; exit 1; }
BASE=$(basename "$SRC")

# 親ディレクトリを基点に tar 化（ディレクトリ・日本語名・階層を保持。mac のゴミは付けない）
PARENT=$(cd "$(dirname "$SRC")" && pwd)
PAYLOAD=$(mktemp -t skel_payload.XXXXXX).tgz
COPYFILE_DISABLE=1 tar -czf "$PAYLOAD" -C "$PARENT" "$BASE"

gcloud compute scp "$PAYLOAD" "$TLJH_VM:/tmp/skel_payload.tgz" --project="$PROJECT" --zone="$ZONE" --quiet

gcloud compute ssh "$TLJH_VM" --project="$PROJECT" --zone="$ZONE" --quiet --command="
    set -e
    if sudo test -e /etc/skel/$BASE; then
        echo 'ERROR: /etc/skel/$BASE は既に存在します。置き換えるなら先に手動で削除してください'
        exit 1
    fi
    tmp=\$(mktemp -d)
    tar -xzf /tmp/skel_payload.tgz -C \"\$tmp\"
    sudo find \"\$tmp/$BASE\" -name '._*' -delete 2>/dev/null || true   # AppleDouble 掃除
    sudo cp -r \"\$tmp/$BASE\" /etc/skel/$BASE
    sudo chown -R root:root /etc/skel/$BASE
    if [ -d \"/etc/skel/$BASE\" ]; then sudo chmod 755 /etc/skel/$BASE; sudo chmod 644 /etc/skel/$BASE/* 2>/dev/null || true
    else sudo chmod 644 /etc/skel/$BASE; fi
    echo '=== 配置後の /etc/skel ==='
    sudo find /etc/skel -mindepth 1 | sed 's|/etc/skel/||' | sort
"
echo "done: /etc/skel/$BASE を配置（以後の初回ログイン者に配られる）"
