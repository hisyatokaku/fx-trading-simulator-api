#!/bin/bash
# ID リストのユーザーを JupyterHub に事前登録する（Admin パネルに表示される状態にする）。
#
# 使い方: bash 08_create_users.sh users/testers.txt
#
# - JupyterHub の REST API（管理者トークン）で作成。既に存在する ID はスキップ（何度実行しても安全）
# - パスワードは設定しない。FirstUseAuthenticator なので本人の初回ログイン時のパスワードが登録される
# - tljh-config の users.allowed は使わない（許可リストを設けない方針を壊すため）
# - Linux ユーザー (jupyter-<id>) とホームは本人の初回ログイン時に TLJH が作る
set -euo pipefail
source "$(dirname "$0")/config.sh"

FILE=${1:?usage: bash 08_create_users.sh <id-list-file>}
# コメント行・空行を除いた ID をスペース区切りに
IDS=$(grep -vE '^\s*(#|$)' "$FILE" | tr '\n' ' ')
[ -n "$IDS" ] || { echo "no ids in $FILE"; exit 1; }
ADMIN=${TLJH_ADMIN_USERS%% *}   # トークン発行に使う管理者（先頭の1人）

gcloud compute ssh "$TLJH_VM" --project="$PROJECT" --zone="$ZONE" --quiet --command="
    set -e
    # 管理者トークンを発行。DB は /opt/tljh/state にあるので必ずそこを cwd にする
    TOKEN=\$(sudo bash -c 'cd /opt/tljh/state && TLJH_INSTALL_PREFIX=/opt/tljh PATH=/opt/tljh/hub/bin:\$PATH \
        /opt/tljh/hub/bin/python3 -m jupyterhub token $ADMIN \
        -f /opt/tljh/hub/lib/python3.10/site-packages/tljh/jupyterhub_config.py 2>/dev/null | tail -1')
    [ -n \"\$TOKEN\" ] || { echo 'failed to get admin token'; exit 1; }
    for u in $IDS; do
        code=\$(curl -s -o /dev/null -w '%{http_code}' -X POST -H \"Authorization: token \$TOKEN\" http://localhost/hub/api/users/\$u)
        case \$code in
            201) echo \"created \$u\" ;;
            409) echo \"exists  \$u\" ;;
            *)   echo \"ERROR   \$u (http \$code)\"; exit 1 ;;
        esac
    done
    echo '--- all users:'
    curl -s -H \"Authorization: token \$TOKEN\" http://localhost/hub/api/users | python3 -c 'import sys,json; print(\" \".join(sorted(u[\"name\"] for u in json.load(sys.stdin))))'
"
