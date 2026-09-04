#!/bin/bash
# TLJH VM のプロビジョニング（VM 初回起動時に startup-script として root で自動実行される）
# 直接実行するものではない。03_tljh_create_vm.sh がメタデータ経由で値を渡す:
#   fx-api-internal-ip : app VM の内部IP
#   tljh-admin-users   : TLJH 管理者ユーザー名（スペース区切り）
#   tljh-user-quota-kb : 参加者1人あたりのディスク上限（KB）
set -euxo pipefail

MARKER=/opt/tljh-provisioned
[ -f "$MARKER" ] && exit 0

META="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
APP_IP=$(curl -sf -H "Metadata-Flavor: Google" "$META/fx-api-internal-ip")
ADMIN_USERS=$(curl -sf -H "Metadata-Flavor: Google" "$META/tljh-admin-users")
QUOTA_KB=$(curl -sf -H "Metadata-Flavor: Google" "$META/tljh-user-quota-kb")

apt-get update
apt-get install -y python3 python3-dev python3-pip curl quota
# GCP カーネルは quota_v2 モジュールを linux-modules-extra に分離している。無いと quotaon が
# "Quota format not supported in kernel" で失敗する（2026-08-29 初回構築時に判明）
apt-get install -y "linux-modules-extra-$(uname -r)"
modprobe quota_v2

# ホームディレクトリを本人以外読めなくする（戦略ノートブックの覗き見防止）。
# Ubuntu 22.04 の既定も 0750 だが、既定値頼みにせず明示する
grep -q '^HOME_MODE' /etc/login.defs \
    && sed -i 's/^HOME_MODE.*/HOME_MODE 0750/' /etc/login.defs \
    || echo 'HOME_MODE 0750' >> /etc/login.defs

# --- TLJH 本体（https://tljh.jupyter.org）。完了まで数分かかる ---
# スペース区切りの管理者リストを --admin フラグ列に変換（例: --admin tonkou --admin kein）
ADMIN_FLAGS=""
for u in $ADMIN_USERS; do ADMIN_FLAGS="$ADMIN_FLAGS --admin $u"; done
# shellcheck disable=SC2086
curl -fL https://tljh.jupyter.org/bootstrap.py | python3 - $ADMIN_FLAGS

TLJH_CONFIG=/opt/tljh/hub/bin/tljh-config

# --- ユーザー毎のメモリ/CPU上限（cgroup で強制。暴走セルから他ユーザーを守る） ---
"$TLJH_CONFIG" set limits.memory 1G
"$TLJH_CONFIG" set limits.cpu 1

# --- 全ユーザーのノートブックに FX_API_BASE_URL を配る ---
# （day1.ipynb は os.environ.get("FX_API_BASE_URL", ...) で参照する）
mkdir -p /opt/tljh/config/jupyterhub_config.d
cat > /opt/tljh/config/jupyterhub_config.d/fx_env.py <<EOF
c.Spawner.environment = {"FX_API_BASE_URL": "http://${APP_IP}:8000"}
EOF

# --- 参加者が使うパッケージを共有ユーザー環境に事前インストール ---
/opt/tljh/user/bin/python3 -m pip install --no-cache-dir \
    requests numpy pandas matplotlib tqdm

# --- ディスククォータ: 1人あたり QUOTA_KB を強制（巨大DLでのディスクフル対策） ---
# ルートFSに usrquota を有効化
if ! grep -q usrquota /etc/fstab; then
    # 列区切りはタブなので [^ ] ではなく [^[:space:]] で options 列だけを掴む（[^ ] だとタブを越えて dump 列に付く）
    sed -i 's|^\(LABEL=cloudimg-rootfs[[:space:]]\+/[[:space:]]\+ext4[[:space:]]\+\)\([^[:space:]]*\)|\1\2,usrquota|' /etc/fstab
    mount -o remount /
    quotacheck -um / || true
    quotaon /
    quotaon -p / | grep -q "user quota on / .* is on"   # 効いていなければここで止める
fi
# TLJH のユーザー (jupyter-*) は動的に作られるため、cron で毎分クォータを適用
cat > /etc/cron.d/tljh-disk-quota <<EOF
* * * * * root for u in \$(getent passwd | cut -d: -f1 | grep '^jupyter-'); do setquota -u "\$u" 0 $QUOTA_KB 0 0 / 2>/dev/null; done
EOF

"$TLJH_CONFIG" reload

touch "$MARKER"
