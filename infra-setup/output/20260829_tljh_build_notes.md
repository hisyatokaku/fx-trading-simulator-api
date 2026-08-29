# 2026-08-29 TLJH VM 初回構築の記録

## 実行したこと
- `03_tljh_create_vm.sh` 実行（ログ: `03_tljh_create_vm_20260829-*.log`）
  - ファイアウォール `allow-tljh-http`（tcp:80）作成
  - 静的 IP `fx-tljh-ip` = **35.243.84.187** 予約・割当
  - VM `fx-tljh`（e2-highmem-8 / Ubuntu 22.04 / 128GB pd-balanced）作成、内部 IP 10.146.15.205
  - app VM 内部 IP 10.146.0.24 をメタデータで引き渡し
- 04 は startup-script として自動実行、約 3 分で `/opt/tljh-provisioned` 作成

## 04 完了後の確認結果
| 項目 | 結果 |
|---|---|
| `tljh-config show` | admin: tonkou, kein / limits.memory 1G / limits.cpu 1 |
| `fx_env.py` | `FX_API_BASE_URL=http://10.146.0.24:8000` |
| `systemctl is-active jupyterhub` | active |
| `http://35.243.84.187/` | 302 → /hub/ |
| TLJH VM → `http://10.146.0.24:8000/docs` | 200（内部ネットワーク疎通 OK） |
| ディスククォータ | **効いていなかった**（下記） |

## 問題: ディスククォータが有効になっていなかった
04 の `quotaon / || true` が失敗を握り潰していた。原因 2 つ。

1. **fstab の sed が間違った列に付けていた**
   `[^ ]*` がタブを越えて dump 列まで掴み、`discard,errors=remount-ro<TAB>0,usrquota 1` になっていた
2. **`quota_v2` カーネルモジュールが無い**
   GCP カーネル（6.8.0-1066-gcp）は `CONFIG_QFMT_V2=m` だが、モジュール本体は
   `linux-modules-extra-<版>` パッケージに分離されていて未インストール。
   `quotaon: Quota format not supported in kernel` で失敗

## VM 上で手動で行った修正（SSH）
```
sudo cp /etc/fstab /etc/fstab.bak
sudo sed -i "s|^LABEL=cloudimg-rootfs.*|LABEL=cloudimg-rootfs\t/\t ext4\tdiscard,errors=remount-ro,usrquota\t0 1|" /etc/fstab
sudo mount -o remount /
sudo apt-get install -y linux-modules-extra-$(uname -r)
sudo modprobe quota_v2
sudo quotacheck -um /
sudo quotaon /
sudo quotaon -p /      # → user quota on / (/dev/root) is on
```

## 修正後の動作確認
- `nobody` に 2GB 設定 → `dd` で 3GB 書き込み → **2.0 GiB (2147479552 bytes) で停止**。クォータ有効
- cron `/etc/cron.d/tljh-disk-quota`（毎分 jupyter-* に 2097152KB 適用）設置済み
- この時点で jupyter-* ユーザーはまだ 0 人（誰もログインしていない）

## スクリプト側への反映（済）
- `04_tljh_provision.sh`
  - `linux-modules-extra-$(uname -r)` インストール + `modprobe quota_v2` 追加
  - sed を `[^[:space:]]*` に修正（VM の GNU sed で pristine 行に対して検証済み）
  - `quotaon / || true` → `quotaon /` + `quotaon -p` で on を確認、効いていなければ失敗で止まる
- `03_04_解説.md` に上記の背景を追記

## 同日追記（13:30 頃）
- [x] tonkou / kein ログイン・パスワード確定（ユーザー実施）
- [x] `05_verify.sh`: ping avg 0.61ms、/health OK、/next 100往復 **1.57s（15.7ms/step）**（ログ `05_verify_20260829-*.log`）
- [x] VM 再起動 → user quota on / quota モジュール自動ロード / jupyterhub active / hub 200。**再起動後も自動で有効**
- [x] `infra-setup/` をコミット（ブランチ infra-setup-tljh）

## 同日追記: テスター ID 5 件を事前登録
- `users/testers.txt` に `tester-<4桁hex>` × 5 を記録、`08_create_users.sh` で Hub に登録（ログ `08_create_users_*.log`）
- 登録は JupyterHub REST API。管理者トークンは **cwd=/opt/tljh/state で** `jupyterhub token` を発行する必要あり
  （別 cwd で実行すると空の sqlite がそこに作られトークンが無効になる。1回やらかして削除済み）
- その後 ID を `tester-1`〜`tester-8` に付け直し（旧 `tester-<hex>` 5 件は REST API の DELETE で削除、未ログインだったのでホーム無し。
  削除スクリプトは誤作動リスクを避けるため置かない方針。消すときは VM 上で手動: Admin パネル or `curl -X DELETE .../hub/api/users/<id>`）
- この時点の `/home` は `jupyter-tonkou` のみ。**kein は未ログイン**（Hub 上には居るがホーム無し）

## 同日追記: 本番参加者 60 名分の ID を登録
- `users/participants.txt`：英数 5 文字 × 60（0 o i l 1 を除外、数字のみは除外、31^5 ≈ 2,860 万通り）
- `08_create_users.sh` で 60 件 `created`（ログ `08_create_users_*.log` 最新）。Hub 上は管理者 2 + tester 8 + 本番 60 = 70 ユーザー
- 全員未ログイン。ID 配布後は早めにログインしてパスワードを確定させる運用

## 次にやること
- [ ] 参加者アカウントでメモリ 1GB / CPU / クォータの体感テスト（リハ 2〜3 人）
- [ ] README が参照する `document/TLJH説明.md` が存在しない → 削除かパス修正
