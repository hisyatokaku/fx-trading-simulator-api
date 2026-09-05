# 負荷テスト用ハーネス

app サーバ（fx-trade-api-ssd）が同時実行にどれだけ耐えるかを測る。
所見 §5-5 / TODO バックログの「負荷テスト」に対応。

## ファイル

| ファイル | 役割 |
|---|---|
| `run_session.py` | 1 セッションを完走し、レイテンシ統計を JSON で出す（最小単位） |
| `run_parallel.py` | N セッションを並列実行し集約。`--sweep` で段階的に負荷を上げる |
| `day1_extracted.py` / `day2_extracted.py` | 教材ノートブックの .py 書き出し（参照用） |

`run_session.py` はノートブック（day2）の `BaseTradingSession` と同じ HTTP
パターン（start → /next を is_complete まで）を、負荷計測に必要な最小限だけ
抜き出したもの。戦略ロジックは持たない（`--strategy noop|fixed` で注文の有無だけ変える）。

## 使い方

```bash
# 単発（1 セッション）
python scripts/loadtest/run_session.py --scenario TEST0 --user latency-check

# 並列 10
python scripts/loadtest/run_parallel.py --concurrency 10 --scenario TEST0

# 段階的に上げて頭打ち点を探す
python scripts/loadtest/run_parallel.py --sweep 1,5,10,20,50 --scenario TEST0
```

## 注意

- **user は許可リスト内の ID**（`latency-check` 等）を使う。EVAL 以外のシナリオは
  同一 user の同時セッションが許容されるので、既定は latency-check を共有する
- **balances が膨らむ**ので、テスト後は `06_truncate_balances.sh` で掃除する
- 本番 VM に対して回すなら**イベント前の無人時間**に。まずステージング推奨
- 完走に時間がかかる（1 セッション ≒ 1,439 tick）。並列数が上がると 1 人あたりも伸びる

## 初期観測（2026-09-06、外部 IP 経由 / e2-medium / noop）

| 並列 | 完走時間(中央値) | /next p50 | /next p95 |
|---|---|---|---|
| 1 | 33.8 s | 23 ms | 27 ms |
| 3 | 58.1 s | 39 ms | 53 ms |

並列 1 → 3 で 1 人あたりの完走が 34s → 58s に伸び、レイテンシも約 1.7 倍。
**e2-medium（2 vCPU）では 3 並列で既に頭打ちの兆候**。50 人同時は要スケールアップ
（所見 §5-5）。TLJH 内部 IP 経由ならレイテンシはさらに下がるはず（別途計測）。
