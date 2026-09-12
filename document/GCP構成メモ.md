# GCP 構成メモ（プロジェクト削除前の記録、2026-09-12）

プロジェクト `fx-itnern` を削除しても同じ構成を再現できるように、手で作ったものだけを記録する。
スクリプト化されている部分は `infra-setup/` を正とし、ここでは差分と手作業だけ書く。

## 全体像

```
参加者ブラウザ ──HTTPS──▶ fx-tljh (JupyterHub)  ──内部NW──▶ fx-trade-api-ssd (FastAPI + Postgres)
                                                                   ▲
fxapp.netlify.app（成績UI）──Netlify proxy /api/* ──外部IP:8000───┘
```

- プロジェクト: `fx-itnern`（削除予定。再構築時は新プロジェクト ID を `infra-setup/config.sh` の `PROJECT` に入れる）
- リージョン/ゾーン: `asia-northeast1` / `asia-northeast1-b`（2 台を同一ゾーンに置く。VM 間 RTT 0.1〜0.5 ms）
- 課金の主因: VM 2 台（停止中はディスクと静的 IP のみ）

## VM 1: app/DB `fx-trade-api-ssd`

| 項目 | 値 |
|---|---|
| マシンタイプ | 平常 e2-medium / イベント中 e2-standard-8（運営手順 §5-5） |
| ブートディスク | `fx-trade-api-ssd-2`、pd-ssd 30 GB、Debian 13（debian-13-trixie）。イベント中に 90% まで逼迫したので次回は 100 GB |
| 静的外部 IP | `fx-trade-api-ip` = 34.146.231.219（リージョン asia-northeast1）。VM 削除時は IP も解放すること |
| 内部 IP | 10.146.0.24（TLJH の `FX_API_BASE_URL` に使う。再構築時は変わる） |
| ネットワークタグ | `fxtrade-api` |
| ファイアウォール | `allow-fxtrade-api-8000`（tcp:8000、0.0.0.0/0）、`allow-fxtrade-api-http`（tcp:80） |
| OS ユーザー | `ky2001`（deploy が SSH する）、`tonkou`（作業用） |
| アプリ配置 | `/home/ky2001/fxtrade-api` に docker compose 一式。`docker-compose.yml` と `.env` は deploy で上書きされない |
| compose の差分 | リポジトリの docker-compose.yml に対し、app サービスへ `UVICORN_WORKERS: "2"`（イベント中 "8"）を追加してある。DB 認証は `POSTGRES_PASSWORD` を 02 スクリプトで初期値から変更済み（値は .env） |
| 起動 | restart ポリシー無し。VM 起動後に `sudo docker compose --project-directory /home/ky2001/fxtrade-api up -d` が必要（次回は `restart: unless-stopped` を付ける） |
| 初期データ | main へのマージで deploy が `alembic upgrade head` と `scripts/seed_data.py`（scenarios / traders / rates の upsert）を実行する。手動なら `python scripts/seed_data.py http://<IP>:8000` |

**再構築手順の要点**: Debian VM を作成 → Docker と docker compose plugin を入れる → リポジトリの Dockerfile / docker-compose.yml / .env を `/home/<user>/fxtrade-api` に置く → `docker compose up -d` → 静的 IP とファイアウォール（tcp:8000）→ deploy.yml の SSH 先ユーザー名と VM 名を合わせる。

## VM 2: TLJH `fx-tljh`

| 項目 | 値 |
|---|---|
| マシンタイプ | e2-highmem-8（8 vCPU / 64 GB。参加者 50 人 × メモリ上限 1 GB） |
| ブートディスク | `fx-tljh`、pd-balanced 128 GB、Ubuntu 22.04 |
| 静的外部 IP | `fx-tljh-ip` = 35.243.84.187 |
| 内部 IP | 10.146.15.205 |
| ネットワークタグ | `tljh` |
| ファイアウォール | `allow-tljh-http`（tcp:80）、`allow-tljh-https`（tcp:443） |
| 作成 | `infra-setup/03_tljh_create_vm.sh`（静的 IP・ファイアウォール・メタデータ・startup-script まで一括） |
| プロビジョニング | `infra-setup/04_tljh_provision.sh` が startup-script として自動実行。TLJH 本体、管理者 tonkou/kein、メモリ 1 GB・CPU 1 コア・ディスク 2 GB の上限、`FX_API_BASE_URL`、参加者用パッケージ |
| メタデータ | `fx-api-internal-ip`（app VM の内部 IP）、`tljh-admin-users`、`tljh-user-quota-kb` |
| HTTPS | 手作業で有効化（2026-09-02、`infra-setup/output/https_enable_20260902-2235.log`）。ドメインは `35-243-84-187.sslip.io`（IP を含む名前なので IP が変われば URL も変わる）。Let's Encrypt、通知先 hisyatokaku2003@gmail.com。`tljh-config set https.enabled true` + `https.letsencrypt.email` + `https.letsencrypt.domains` |
| ユーザー登録 | `infra-setup/08_create_users.sh users/participants.txt`（ID 一覧はリポジトリ管理）。パスワードは初回ログイン時に本人が設定 |
| 教材配布 | `10_place_in_skel.sh`（未ログイン者向け）と `11_distribute_to_homes.sh`（ログイン済み向け） |

## IAM / GitHub Actions

| 項目 | 値 |
|---|---|
| サービスアカウント | `github-actions-deploy@fx-itnern.iam.gserviceaccount.com`（ロール `roles/compute.instanceAdmin.v1`） |
| 認証方式 | SA の JSON キーを GitHub Secrets `GCP_CREDENTIALS` に登録。`google-github-actions/auth@v3` の `credentials_json` で使用 |
| デプロイ | `.github/workflows/deploy.yml`: main へ push → tar でリポジトリを `ky2001@fx-trade-api-ssd` に送る → build → alembic → compose up → seed → e2e |

**再構築時**: 新プロジェクトで SA を作り直し、`compute.instanceAdmin.v1` を付与、新しい JSON キーを `GCP_CREDENTIALS` に再登録。deploy.yml の `--project`、VM 名、SSH ユーザーを更新。

## 外部サービス（GCP 外だが IP に依存する）

- **Netlify（fxapp.netlify.app）**: WebUI リポジトリの `netlify.toml` が `/api/*` を `http://34.146.231.219:8000/api/:splat` に中継。app の IP が変われば要更新
- **day2.ipynb**: `BASE_URL` の既定値に外部 IP `http://34.146.231.219:8000` を直書き（TLJH では環境変数 `FX_API_BASE_URL` で内部 IP に上書き）
- **運営手順 / 参加者向け手順 / 投影内容**: TLJH の URL と app の IP を記載

## プロジェクト削除前に控えるもの

1. DB のダンプ（提出結果を残すなら）: `docker compose exec db pg_dump -U fxtrade fxtrade | gzip > fxtrade_YYYYMMDD.sql.gz`
2. `/home/ky2001/fxtrade-api/.env` と `docker-compose.yml`（DB パスワードと UVICORN_WORKERS の差分）
3. TLJH の参加者ホーム（必要なら `tar` で `/home/jupyter-*` を退避）
4. SA の JSON キーは再発行できるので保存不要。GitHub Secrets は新プロジェクト用に差し替える

## 再構築の順序

1. 新プロジェクト作成 → Compute Engine API 有効化 → `config.sh` の `PROJECT` を更新
2. app/DB VM を作成し compose を起動（上記「VM 1」）→ 静的 IP 予約 → `seed_data.py`
3. SA と GitHub Secrets → deploy.yml を更新して main に push（自動デプロイの確認）
4. `03_tljh_create_vm.sh` → 起動時プロビジョニング完了を待つ → HTTPS 有効化（sslip.io の名前は新 IP に合わせる）
5. `08_create_users.sh` → `10_place_in_skel.sh` で教材配置 → `05_verify.sh`
6. Netlify の proxy 先と各ドキュメントの IP / URL を更新
