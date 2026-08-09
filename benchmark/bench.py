#!/usr/bin/env python3
"""API レイテンシ計測スクリプト。

同一エンドポイントを N 回呼び、1回ごとの所要時間をすべて記録して統計を出す。

計測方法:
  1. GET /health を HEALTH_N 回呼ぶ
     - サーバ処理がほぼゼロのエンドポイントなので、これが「ネットワーク往復時間」の基準値になる
  2. POST /api/trade/start/DEMO_2016/testuser でセッションを1つ作る
  3. POST /api/trade/next（毎日 JPY→USD 1000円の両替）を STEPS 回呼ぶ
     - 参加者向けノートブックのループと同じ操作
  4. 「trade/next の時間 − /health の時間 ≒ サーバ内部の処理時間」として分離する

記録:
  - results/<label>_raw.csv   … 全リクエストの生データ（1行 = 1リクエスト）
  - results/summary.csv       … 統計サマリ（追記式。全環境の比較はこれを見る）

注意:
  - requests.Session() で接続を使い回す（keep-alive）。毎回 TCP/TLS を張り直すと
    その分が上乗せされ、純粋な比較にならないため。
  - 統計は平均だけでなく中央値・p95 も出す。外れ値（初回接続やGCの揺れ）の影響を
    見分けるため。

使い方:
  python3 bench.py <base_url> <label> [steps]
  例: python3 bench.py https://app-production-7488.up.railway.app railway 50
"""

import csv
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

HEALTH_N = 20  # /health の計測回数

def measure(fn):
    """関数 fn の実行時間をミリ秒で返す"""
    t0 = time.perf_counter()
    resp = fn()
    ms = (time.perf_counter() - t0) * 1000
    return ms, resp


def stats_row(label, endpoint, xs, base_url):
    p95 = statistics.quantiles(xs, n=20)[-1] if len(xs) >= 20 else max(xs)
    return {
        "measured_at": datetime.now().isoformat(timespec="seconds"),
        "label": label,
        "endpoint": endpoint,
        "n": len(xs),
        "mean_ms": round(statistics.mean(xs), 1),
        "median_ms": round(statistics.median(xs), 1),
        "min_ms": round(min(xs), 1),
        "max_ms": round(max(xs), 1),
        "p95_ms": round(p95, 1),
        "base_url": base_url,
    }


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    base_url = sys.argv[1].rstrip("/")
    label = sys.argv[2]
    steps = int(sys.argv[3]) if len(sys.argv) > 3 else 50

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    s = requests.Session()
    raw = []  # (endpoint, index, ms, http_status)

    # --- 0. ウォームアップ（初回の接続確立・TLS分は計測に含めない） ---
    s.get(f"{base_url}/health", timeout=30)

    # --- 1. /health を HEALTH_N 回 ---
    health_times = []
    for i in range(HEALTH_N):
        ms, r = measure(lambda: s.get(f"{base_url}/health", timeout=30))
        health_times.append(ms)
        raw.append(("GET /health", i + 1, round(ms, 2), r.status_code))

    # --- 2. セッション開始 ---
    r = s.post(f"{base_url}/api/trade/start/DEMO_2016/testuser", timeout=30)
    r.raise_for_status()
    session_id = r.json()["id"]

    # --- 3. /api/trade/next を steps 回 ---
    body = {
        "session_id": session_id,
        "exchange_requests": [
            {"currency_from": "JPY", "currency_to": "USD", "amount": 1000}
        ],
    }
    step_times = []
    for i in range(steps):
        ms, r = measure(lambda: s.post(f"{base_url}/api/trade/next", json=body, timeout=60))
        step_times.append(ms)
        raw.append(("POST /api/trade/next", i + 1, round(ms, 2), r.status_code))
        if r.status_code != 200 or r.json().get("is_complete"):
            break

    # --- 4. 生データを CSV に保存 ---
    raw_path = results_dir / f"{label}_raw.csv"
    with open(raw_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["endpoint", "request_no", "elapsed_ms", "http_status"])
        w.writerows(raw)

    # --- 5. サマリを表示 & summary.csv に追記 ---
    rows = [
        stats_row(label, "GET /health", health_times, base_url),
        stats_row(label, "POST /api/trade/next", step_times, base_url),
    ]
    summary_path = results_dir / "summary.csv"
    write_header = not summary_path.exists()
    with open(summary_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if write_header:
            w.writeheader()
        w.writerows(rows)

    print(f"=== {label} ({base_url}) ===")
    for row in rows:
        print(
            f"{row['endpoint']:<22} n={row['n']:>3} "
            f"mean={row['mean_ms']:>7.1f}ms median={row['median_ms']:>7.1f}ms "
            f"min={row['min_ms']:>7.1f}ms max={row['max_ms']:>7.1f}ms p95={row['p95_ms']:>7.1f}ms"
        )
    proc = statistics.median(step_times) - statistics.median(health_times)
    print(f"サーバ内部処理の推定値 (trade/next中央値 - health中央値): {proc:.1f}ms")
    print(f"生データ: {raw_path}")


if __name__ == "__main__":
    main()
