#!/usr/bin/env python
"""N セッションを並列実行し、app サーバの負荷耐性を測る。

run_session.py の run_one を並列に走らせ、レイテンシとエラーを集約する。
50 人同時などをシミュレートして、1 人あたりの完走時間がどれだけ伸びるか、
どこで頭打ちになるかを見るための土台。

使い方:
    python scripts/loadtest/run_parallel.py --concurrency 10 \
        --scenario TEST0 --base http://34.146.231.219:8000

    # 段階的にN を増やす（頭打ち点を探す）
    python scripts/loadtest/run_parallel.py --sweep 1,5,10,20,50

注意:
    - user は許可リスト内の ID を使う（latency-check 等）。並列時は user を
      連番で振る（--user-prefix）が、EVAL 以外のシナリオは同一 user の同時
      セッションが許容されるため、既定は全並列で latency-check を共有する
    - balances が膨らむので、負荷テスト後は 06_truncate_balances.sh で掃除する
    - まずステージングか、本番ならイベント前の無人時間に実行すること
"""
import argparse
import concurrent.futures
import json
import statistics
import time

from run_session import run_one


def run_batch(base, scenario, users, strategy, timeout, concurrency):
    """concurrency 個を同時に走らせ、結果リストを返す。"""
    t0 = time.perf_counter()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = [
            ex.submit(run_one, base, scenario, users[i % len(users)], strategy, timeout)
            for i in range(concurrency)
        ]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())
    wall = time.perf_counter() - t0
    return results, wall


def summarize(results, wall, concurrency):
    ok = [r for r in results if r["ok"]]
    completions = [r["total_seconds"] for r in ok]
    p50s = [r["latency_ms"]["p50"] for r in ok if "latency_ms" in r]
    p95s = [r["latency_ms"]["p95"] for r in ok if "latency_ms" in r]
    return {
        "concurrency": concurrency,
        "sessions_ok": len(ok),
        "sessions_failed": len(results) - len(ok),
        "wall_seconds": round(wall, 1),
        "completion_seconds": {
            "min": round(min(completions), 1) if completions else None,
            "median": round(statistics.median(completions), 1) if completions else None,
            "max": round(max(completions), 1) if completions else None,
        },
        "per_request_latency_ms": {
            "median_of_p50": round(statistics.median(p50s), 1) if p50s else None,
            "median_of_p95": round(statistics.median(p95s), 1) if p95s else None,
        },
        "errors": [r["error_detail"] for r in results if r["error_detail"]][:5],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://34.146.231.219:8000")
    ap.add_argument("--scenario", default="TEST0")
    ap.add_argument("--strategy", choices=["noop", "fixed"], default="noop")
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--users", default="latency-check",
                    help="カンマ区切りの user_id。並列セッションに順に割り当てる")
    ap.add_argument("--concurrency", type=int, default=10)
    ap.add_argument("--sweep", default=None,
                    help="カンマ区切りの並列数リスト。指定すると段階的に実行（例: 1,5,10,20,50）")
    args = ap.parse_args()

    users = [u.strip() for u in args.users.split(",") if u.strip()]
    levels = [int(x) for x in args.sweep.split(",")] if args.sweep else [args.concurrency]

    for n in levels:
        results, wall = run_batch(args.base, args.scenario, users, args.strategy, args.timeout, n)
        print(json.dumps(summarize(results, wall, n), ensure_ascii=False))


if __name__ == "__main__":
    main()
