#!/usr/bin/env python
"""1 セッションを最後まで実行し、レイテンシ統計を出力する（負荷テストの最小単位）。

ノートブック（day2）の BaseTradingSession と同じ HTTP パターン
（POST /api/trade/start → POST /api/trade/next を is_complete まで）を、
負荷計測に必要な最小限だけ抜き出したもの。戦略ロジックは持たず、毎 tick で
指定された注文（既定は「何もしない」）を送るだけ。app サーバの生の処理能力を測る。

使い方:
    python scripts/loadtest/run_session.py [--base URL] [--scenario NAME]
                                           [--user ID] [--strategy noop|fixed]

例:
    python scripts/loadtest/run_session.py --scenario TEST0 --user latency-check
    python scripts/loadtest/run_session.py --base http://34.146.231.219:8000 \
        --scenario TEST1 --user tester-1 --strategy fixed

出力: JSON 1 行（steps / 総時間 / スループット / レイテンシ p50・p95・p99・max /
      エラー数）。並列ランナー（run_parallel.py）がこれを集約する前提の形。
"""
import argparse
import json
import statistics
import sys
import time

import requests


def build_order(strategy: str, balances: dict) -> list:
    """毎 tick 送る注文を返す。負荷の形を変えるためのフック。"""
    if strategy == "fixed":
        # 残高がある範囲で JPY→USD, JPY→AUD を少額。注文処理も含めた負荷になる
        if balances.get("JPY", 0) >= 2000:
            return [
                {"currency_from": "JPY", "currency_to": "USD", "amount": 1000},
                {"currency_from": "JPY", "currency_to": "AUD", "amount": 1000},
            ]
        return []
    # noop: 注文なしで tick だけ進める（最小負荷 = 純粋な往復コスト）
    return []


def run_one(base: str, scenario: str, user: str, strategy: str, timeout: float) -> dict:
    http = requests.Session()  # keep-alive
    start_url = f"{base}/api/trade/start/{scenario}/{user}"
    next_url = f"{base}/api/trade/next"

    result = {
        "scenario": scenario, "user": user, "strategy": strategy,
        "ok": False, "steps": 0, "errors": 0, "error_detail": None,
    }

    t_start = time.perf_counter()
    try:
        r = http.post(start_url, timeout=timeout)
        r.raise_for_status()
    except Exception as e:
        result["error_detail"] = f"start failed: {e}"
        result["errors"] += 1
        return result

    state = r.json()
    session_id = state["id"]
    balances = state["balances"]
    latencies = []  # 各 /next の所要時間（秒）

    while not state.get("is_complete", False):
        body = {"session_id": session_id, "exchange_requests": build_order(strategy, balances)}
        t0 = time.perf_counter()
        try:
            r = http.post(next_url, json=body, timeout=timeout)
            r.raise_for_status()
        except Exception as e:
            result["errors"] += 1
            result["error_detail"] = f"next failed at step {result['steps']}: {e}"
            break
        latencies.append(time.perf_counter() - t0)
        state = r.json()
        balances = state["balances"]
        result["steps"] += 1

    total = time.perf_counter() - t_start
    result["ok"] = result["errors"] == 0 and result["steps"] > 0
    result["total_seconds"] = round(total, 3)
    if latencies:
        latencies_ms = sorted(x * 1000 for x in latencies)
        result["throughput_req_per_s"] = round(len(latencies) / sum(latencies), 1)
        result["latency_ms"] = {
            "mean": round(statistics.mean(latencies_ms), 2),
            "p50": round(statistics.median(latencies_ms), 2),
            "p95": round(latencies_ms[int(len(latencies_ms) * 0.95)], 2),
            "p99": round(latencies_ms[min(int(len(latencies_ms) * 0.99), len(latencies_ms) - 1)], 2),
            "max": round(latencies_ms[-1], 2),
        }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://34.146.231.219:8000")
    ap.add_argument("--scenario", default="TEST0")
    ap.add_argument("--user", default="latency-check")
    ap.add_argument("--strategy", choices=["noop", "fixed"], default="noop")
    ap.add_argument("--timeout", type=float, default=30.0)
    args = ap.parse_args()

    res = run_one(args.base, args.scenario, args.user, args.strategy, args.timeout)
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(0 if res["ok"] else 1)


if __name__ == "__main__":
    main()
