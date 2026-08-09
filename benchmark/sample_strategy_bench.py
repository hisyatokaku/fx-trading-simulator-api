#!/usr/bin/env python3
"""2025年イベント仕様書のサンプル戦略を、現在の API で実行してレイテンシを計測する。

document/仕様書_2025.ipynb の FixedStrategySession（毎日 JPY→USD 1000円 +
JPY→AUD 1000円）を現在の Python 版 API に移植したもの。API の呼び方も仕様書に
忠実に再現している:
  - 初期化: POST /api/trade/start + 過去10営業日分の GET /api/rate（10リクエスト）
  - 毎日:   POST /api/trade/next を完走（is_complete）まで繰り返す
  - 仕様書と同じく素の requests を使う（keep-alive なし = 毎回 TCP/TLS 接続。
    参加者が実際に体験する条件に合わせるため）

記録: 全 API 呼び出しの所要時間を results/<label>_strategy_raw.csv に保存し、
サマリを results/strategy_summary.csv に追記する。

使い方:
  python3 sample_strategy_bench.py <base_url> <label> [scenario]
  例: python3 sample_strategy_bench.py http://34.84.182.200:8000 gcp-vm DEMO_2016
"""

import csv
import statistics
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

USER_ID = "testuser"


class Timer:
    """API 呼び出しごとの所要時間を記録する"""

    def __init__(self):
        self.records = []  # (kind, ms, http_status)

    def call(self, kind, fn):
        t0 = time.perf_counter()
        resp = fn()
        ms = (time.perf_counter() - t0) * 1000
        self.records.append((kind, round(ms, 2), resp.status_code))
        return resp


def last_n_business_days(end: datetime, n: int):
    days, current = [], end
    while len(days) < n:
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)
    return list(reversed(days))


class FixedStrategySession:
    """仕様書の FixedStrategySession の移植版（毎日 JPY→USD/AUD 各1000円）"""

    def __init__(self, base_url, scenario, timer):
        self.base_url = base_url
        self.timer = timer
        r = timer.call("start", lambda: requests.post(
            f"{base_url}/api/trade/start/{scenario}/{USER_ID}", timeout=60))
        r.raise_for_status()
        info = r.json()
        self.session_id = info["id"]
        self.is_complete = info["is_complete"]
        self.current_datetime = info["current_datetime"]
        self.balances = info["balances"]
        # 仕様書どおり、開始前10営業日分のレート履歴を取得（存在しない日はスキップ）
        self.rate_history = {}
        start = datetime.fromisoformat(self.current_datetime)
        for day in last_n_business_days(start, 10):
            r = self.timer.call("rate_history", lambda d=day: requests.get(
                f"{base_url}/api/rate/{d.strftime('%Y-%m-%dT%H:%M:%S')}", timeout=60))
            if r.status_code == 200:
                for currency, rate in r.json()["rates"].items():
                    self.rate_history.setdefault(currency, []).append(float(rate))

    def strategy(self):
        return [
            {"currency_from": "JPY", "currency_to": "USD", "amount": 1000},
            {"currency_from": "JPY", "currency_to": "AUD", "amount": 1000},
        ]

    def proceed_one_day(self):
        body = {"session_id": self.session_id, "exchange_requests": self.strategy()}
        r = self.timer.call("next", lambda: requests.post(
            f"{self.base_url}/api/trade/next", json=body, timeout=60))
        r.raise_for_status()
        info = r.json()
        self.current_datetime = info["current_datetime"]
        self.balances = info["balances"]
        self.is_complete = info["is_complete"]
        for currency, rate in info.get("rates", {}).items():
            self.rate_history.setdefault(currency, []).append(float(rate))
        return info

    def proceed_to_end(self):
        info = None
        while not self.is_complete:
            info = self.proceed_one_day()
        return info


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    base_url = sys.argv[1].rstrip("/")
    label = sys.argv[2]
    scenario = sys.argv[3] if len(sys.argv) > 3 else "DEMO_2016"

    timer = Timer()
    wall_t0 = time.perf_counter()
    session = FixedStrategySession(base_url, scenario, timer)
    final = session.proceed_to_end()
    wall_seconds = time.perf_counter() - wall_t0

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    raw_path = results_dir / f"{label}_strategy_raw.csv"
    with open(raw_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["call_no", "kind", "elapsed_ms", "http_status"])
        w.writerows((i + 1, *rec) for i, rec in enumerate(timer.records))

    next_times = [ms for kind, ms, _ in timer.records if kind == "next"]
    summary_path = results_dir / "strategy_summary.csv"
    write_header = not summary_path.exists()
    with open(summary_path, "a", newline="") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["measured_at", "label", "scenario", "total_api_calls",
                        "next_calls", "next_median_ms", "next_mean_ms",
                        "wall_seconds", "base_url"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), label, scenario,
                    len(timer.records), len(next_times),
                    round(statistics.median(next_times), 1),
                    round(statistics.mean(next_times), 1),
                    round(wall_seconds, 1), base_url])

    print(f"=== サンプル戦略（Fixed）完走: {label} / {scenario} ===")
    print(f"API 呼び出し総数     : {len(timer.records)}回"
          f"（start 1 + rate_history {sum(1 for k, _, _ in timer.records if k == 'rate_history')}"
          f" + next {len(next_times)}）")
    print(f"/next 1回あたり      : 中央値 {statistics.median(next_times):.1f}ms"
          f" / 平均 {statistics.mean(next_times):.1f}ms"
          f" / 最小 {min(next_times):.1f}ms / 最大 {max(next_times):.1f}ms")
    print(f"戦略の完走時間       : {wall_seconds:.1f}秒")
    if final:
        print(f"最終 JPY 資産        : {float(final['jpy_balance']):,.0f}円")
    print(f"生データ: {raw_path}")


if __name__ == "__main__":
    main()
