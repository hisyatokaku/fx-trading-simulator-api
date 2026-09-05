#!/bin/bash
# JupyterHub 参加者のパスワードをリセットする（FirstUseAuthenticator）。
#
# 仕組み: FirstUseAuthenticator はパスワードを /opt/tljh/state/passwords.dbm に保存し、
#   「キーが無ければ次回ログイン時に入力したパスワードを新規登録する」動作をする。
#   よって dbm から該当ユーザーのキーだけ削除すれば、本人が次のログインで
#   好きなパスワードを再設定できる。ホーム・作業ファイルは一切消えない。
#
# 使い方: bash infra-setup/09_reset_password.sh <ID> [<ID> ...]
#   例:    bash infra-setup/09_reset_password.sh tester-3
#          bash infra-setup/09_reset_password.sh ckym3 rqfb2
#
# 実行後: 対象者に「もう一度ログインし、新しいパスワード（7 文字以上）を入力してください。
#         それがそのまま新しいパスワードになります。作業ファイルは残っています」と案内する。
set -euo pipefail
source "$(dirname "$0")/config.sh"

[ "$#" -ge 1 ] || { echo "usage: bash 09_reset_password.sh <ID> [<ID> ...]"; exit 1; }
IDS="$*"

gcloud compute ssh "$TLJH_VM" --project="$PROJECT" --zone="$ZONE" --quiet --command="
    sudo /opt/tljh/hub/bin/python3 - $IDS <<'PYEOF'
import sys, dbm
DB = '/opt/tljh/state/passwords.dbm'
ids = sys.argv[1:]
d = dbm.open(DB, 'c')
try:
    existing = {k.decode() for k in d.keys()}
    for uid in ids:
        if uid in existing:
            del d[uid]
            print(f'reset    {uid} (次回ログインで再設定)')
        else:
            print(f'skip     {uid} (未ログイン=まだパスワード未設定。リセット不要)')
finally:
    d.close()
PYEOF
"
echo "done: 対象者に「再ログインして新パスワードを入力」と案内してください（作業ファイルは残ります）"
