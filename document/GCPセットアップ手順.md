# GCP セットアップ手順（fx-itnern プロジェクト）

FXトレーディングシミュレータを GCP 上で app + DB 同居構成でホストするための手順書。
2026-08 に実際に構築した内容の記録でもある（現行環境: `fx-trade-api-ssd`）。

## 構成

```
GCE VM 1台（asia-northeast1-b, e2-medium, Debian 12）
├─ docker compose（リポジトリの docker-compose.yml をそのまま使用）
│   ├─ app: FastAPI（port 8000、外部公開）
│   └─ db : PostgreSQL 15（VM内のみ）
└─ JupyterLab（port 8888、localhost バインド・SSHトンネルでのみアクセス）
```

app と DB を同一 VM に置くのが要点。`/api/trade/next` は1回に SQL を15往復するため、
DB が遠いと致命的に遅くなる（実測: Railway 約1000ms/step ↔ 同居 約20ms/step。
詳細は `benchmark/README.md`）。

## 0. 前提

```bash
gcloud auth login                     # 自分のアカウントでログイン
gcloud config set project fx-itnern   # ※プロジェクトIDはタイポ込みで fx-itnern が正
gcloud services enable compute.googleapis.com   # 初回のみ
```

## 1. VM 作成

```bash
gcloud compute instances create <VM名> \
  --zone=asia-northeast1-b \
  --machine-type=e2-medium \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=30GB
```

- 検証用途は e2-medium（2vCPU/4GB、約$0.04/h ≈ 150円/日）で十分
- イベント本番で JupyterHub 50人同居まで載せるなら e2-standard-16 等に上げる

## 2. Docker などのインストール

```bash
gcloud compute ssh <VM名> --zone=asia-northeast1-b --command="
  curl -fsSL https://get.docker.com | sudo sh
  sudo apt-get install -y git python3-venv"
```

## 3. リポジトリ取得と起動

```bash
# クローン（公開の GitHub フォークなら https で鍵不要。GitLab から取る場合は
# ssh-agent forwarding: gcloud compute ssh --ssh-flag=-A で秘密鍵を VM に置かずに済む）
gcloud compute ssh <VM名> --zone=asia-northeast1-b --command="
  git clone https://github.com/hisyatokaku/fx-trading-simulator-api.git fxtrade-api
  cd fxtrade-api
  sudo docker compose up -d --build
  sudo docker compose exec -T app alembic upgrade head          # マイグレーション
  sudo docker compose exec -T app python scripts/seed_data.py http://localhost:8000  # CSV投入
  sudo docker update --restart unless-stopped fxtrade-api-app-1 fxtrade-api-db-1     # VM再起動後も自動起動
  curl -s http://localhost:8000/health"
```

`{"status":"healthy"}` が出れば OK。

## 4. API の外部公開（port 8000）

```bash
gcloud compute firewall-rules create allow-fxtrade-api-8000 \
  --direction=INGRESS --action=ALLOW --rules=tcp:8000 \
  --source-ranges=0.0.0.0/0 --target-tags=fxtrade-api
gcloud compute instances add-tags <VM名> --tags=fxtrade-api --zone=asia-northeast1-b
```

注意: API に認証は無いので、使わない期間は VM を停止しておくこと。

## 5. 静的 IP（外部 IP の固定）

VM の外部 IP はデフォルトでは動的で、停止→起動のたびに変わる。使用中の IP を
そのままの番号で静的に昇格できる（無停止・書き換え不要）:

```bash
gcloud compute addresses create fx-trade-api-ip \
  --addresses=<現在の外部IP> --region=asia-northeast1
# 確認（IN_USE になっていること）
gcloud compute addresses describe fx-trade-api-ip --region=asia-northeast1
```

- 現行環境では `fx-trade-api-ip` = **34.146.231.219** を予約済み（2026-08-21）
- 費用は約 $0.005/h（月500円強）。**IP を使わなくなっても、解放するまで課金される**:
  `gcloud compute addresses delete fx-trade-api-ip --region=asia-northeast1`

## 6. JupyterLab（管理者用・非公開）

```bash
gcloud compute ssh <VM名> --zone=asia-northeast1-b --command="
  python3 -m venv ~/jupyterenv
  ~/jupyterenv/bin/pip install jupyterlab requests matplotlib numpy pandas"
# systemd サービス化（TOKEN は openssl rand -hex 16 などで生成）
# /etc/systemd/system/jupyter.service:
#   ExecStart=/home/<user>/jupyterenv/bin/jupyter lab --no-browser \
#     --ip=127.0.0.1 --port=8888 --ServerApp.token=<TOKEN> --notebook-dir=/home/<user>
#   Restart=on-failure / User=<user> / WantedBy=multi-user.target
sudo systemctl daemon-reload && sudo systemctl enable --now jupyter
```

アクセスは SSH トンネルのみ（Jupyter は任意コード実行できるため公開しない）:

```bash
gcloud compute ssh <VM名> --zone=asia-northeast1-b -- -N -L 8888:localhost:8888
# → ブラウザで http://localhost:8888/lab?token=<TOKEN>
```

参加者50人に配る場合はこの単人用 Jupyter ではなく TLJH（The Littlest JupyterHub）を使う。

## 7. Colab Enterprise から叩く場合の接続先

- ランタイムのリージョンは **asia-northeast1（東京）** にする（レイテンシが数msになる）
- `default` テンプレートのランタイムは VPC 未接続なので **外部IP** を使う:
  `BASE_URL = 'http://34.146.231.219:8000'`
- ランタイムテンプレートで VPC（default ネットワーク / asia-northeast1）を指定した場合は
  **内部IP**（例: `http://10.146.0.24:8000`）が使え、VPC 内で完結する。内部IPは VM を
  削除しない限り変わらない

## 8. 起動・停止・後片付け

```bash
gcloud compute instances stop  <VM名> --zone=asia-northeast1-b   # データは残る。課金はディスクのみ
gcloud compute instances start <VM名> --zone=asia-northeast1-b
gcloud compute instances delete <VM名> --zone=asia-northeast1-b  # 完全削除
```

レイテンシの検証方法は `benchmark/README.md` と `benchmark/レイテンシ計測.ipynb` を参照。
