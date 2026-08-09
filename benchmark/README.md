# API レイテンシ計測記録

「`/api/trade/next` を1000回往復するループがなぜ遅いのか」「app・DB・クライアントを
同一ロケーションに置けば解決するのか」を検証した記録。

## 計測方法

[`bench.py`](bench.py) を使用。同一エンドポイントを N 回呼び、**1回ごとの所要時間を
すべて CSV に記録**した上で平均・中央値・p95 を算出する。

1. `GET /health` × 20回 — サーバ処理がほぼゼロなので **ネットワーク往復時間の基準値**
2. `POST /api/trade/start/DEMO_2016/testuser` — セッション作成（参加者ガイドと同じ）
3. `POST /api/trade/next` × 最大30回 — 参加者ノートブックのループと同じ操作
4. **`trade/next − /health` ≒ サーバ内部の処理時間** として分離

接続は `requests.Session()` で使い回し（keep-alive）、初回接続はウォームアップとして
計測から除外。時間計測は `time.perf_counter()`。

再現方法:

```bash
python3 bench.py <base_url> <ラベル> [ステップ数]
# 例
python3 bench.py https://app-production-7488.up.railway.app railway-prod 30
python3 bench.py http://localhost:8000 local-mac 30
```

## 計測環境（2026-08-03 実施）

| ラベル | クライアント位置 | サーバ位置 | app↔DB |
|---|---|---|---|
| `railway-prod` | 自宅 Mac（日本） | Railway 本番（米国と推定） | Railway 内部（構成不明） |
| `local-mac` | Mac | 同じ Mac 上の docker-compose | 同一マシン |
| `gcp-vm-tokyo` | GCE VM 内 | 同じ VM 上の docker-compose | 同一マシン |

- GCE VM: `fxbench-vm`（プロジェクト `fx-itnern` / asia-northeast1-b / e2-medium / Debian 12）
- コードは全環境とも GitLab `main`（6e97d98）、データは `scripts/seed_data.py` で
  同一 CSV（レート2751件）を投入

## 結果（results/summary.csv より）

`POST /api/trade/next` 1ステップの所要時間:

| 環境 | 平均 | 中央値 | 最小〜最大 | ネットワーク基準値(/health中央値) | サーバ内部処理の推定値 |
|---|---|---|---|---|---|
| railway-prod | 971ms | 1046ms | 189〜1799ms | 122ms | **924ms** |
| local-mac | 6.7ms | 6.2ms | 5.6〜21.6ms | 1.6ms | 4.6ms |
| gcp-vm-tokyo | 25.8ms | 21.5ms | 18.8〜93.8ms | 1.7ms | 19.8ms |

生データ（全リクエスト個別の値）: [`results/railway-prod_raw.csv`](results/railway-prod_raw.csv) /
[`results/local-mac_raw.csv`](results/local-mac_raw.csv) /
[`results/gcp-vm-tokyo_raw.csv`](results/gcp-vm-tokyo_raw.csv)

## 解釈

- Railway の1ステップ約1秒のうち、クライアント↔サーバのネットワークは122msだけ。
  残り**約920msはサーバ側**で消費されている
- 同一コード・同一データを DB と同居させて動かすと、サーバ内部処理は **4.6ms（Mac）/
  19.8ms（e2-medium）** しかない。つまり Railway の920msはアプリの計算ではなく、
  **app↔DB 間のネットワーク遅延**（1ステップに7〜10回ある DB クエリ × 往復約130ms）
  とみられる
- 結論: **app・DB・クライアントを同一ロケーションに置けば、1000往復は
  約17分 → 約25秒（e2-medium）〜6秒（高性能機）** になる
