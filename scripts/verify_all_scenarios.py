#!/usr/bin/env python
"""Run every scenario end-to-end against a live instance and report problems.

For each scenario the script starts a session, buys a little of every
foreign currency on the first tick and every 100 ticks, sells 30% of every
foreign holding back to JPY on the ticks in between, and steps to the end. It checks, per tick, that the server returned a rate for
all 13 foreign currencies and a balance for all 14 currencies, and at the
end that the session completed with the expected number of ticks and a
positive JPY valuation.

Usage:
    python scripts/verify_all_scenarios.py <user_id> [base_url] [--workers N]
        [--only NAME,NAME...] [--currencies USD,EUR,...]

Scenario names default to every row of data/scenarios.csv. EVAL scenarios
count as a submission for <user_id>, so use an admin/test ID. TUTORIAL
scenarios only carry USD rates by design: check them with
--only TUTORIAL1,TUTORIAL2,TUTORIAL3 --currencies USD.

Note: with 4 workers on e2-medium the server tops out around 50 ticks/s in
total, so a full run takes 15-20 minutes.
"""

import argparse
import csv
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests

ALL_FOREIGN = ["USD", "EUR", "GBP", "AUD", "NZD", "CAD", "CHF",
               "TRY", "ZAR", "MXN", "NOK", "SEK", "HKD"]
ALL = ["JPY"] + ALL_FOREIGN
DATA_DIR = Path(__file__).parent.parent / "data"


def run_one(name: str, user_id: str, base_url: str, FOREIGN: list[str]) -> dict:
    http = requests.Session()
    t0 = time.time()
    r = http.post(f"{base_url}/api/trade/start/{name}/{user_id}", timeout=60)
    if r.status_code != 200:
        return {"scenario": name, "ok": False, "error": f"start {r.status_code}: {r.text[:120]}"}
    s = r.json()
    sid = s["id"]
    start = datetime.fromisoformat(s["start_datetime"])
    end = datetime.fromisoformat(s["end_datetime"])
    expected_ticks = int((end - start).total_seconds() // s["time_interval_seconds"])
    problems: list[str] = []
    ticks = 0
    missing_rate_ticks = 0
    while not s.get("is_complete"):
        ticks += 1
        bal = s.get("balances", {})
        if ticks == 1 or ticks % 100 == 50:
            # buy a little of every foreign currency
            reqs = [{"currency_from": "JPY", "currency_to": c, "amount": 1000} for c in FOREIGN]
        elif ticks % 100 == 0:
            # sell 30% of every foreign holding back to JPY
            reqs = [{"currency_from": c, "currency_to": "JPY", "amount": bal.get(c, 0) * 0.3}
                    for c in FOREIGN if bal.get(c, 0) > 0]
        else:
            reqs = []
        r = http.post(f"{base_url}/api/trade/next",
                      json={"session_id": sid, "exchange_requests": reqs}, timeout=60)
        if r.status_code != 200:
            problems.append(f"tick {ticks}: next {r.status_code}: {r.text[:120]}")
            break
        s = r.json()
        miss = [c for c in FOREIGN if c not in s.get("rates", {})]
        if miss:
            missing_rate_ticks += 1
            if len(problems) < 5:
                problems.append(f"tick {ticks} {s['current_datetime']}: no rate for {','.join(miss)}")
        missb = [c for c in ALL if c not in s.get("balances", {})]
        if missb and len(problems) < 5:
            problems.append(f"tick {ticks}: no balance for {','.join(missb)}")
        if reqs and len(s.get("trades", [])) != len(reqs) and len(problems) < 5:
            problems.append(f"tick {ticks}: only {len(s.get('trades', []))}/{len(reqs)} trades executed")
        if ticks > expected_ticks + 5:
            problems.append("session did not complete at expected end")
            break
    if ticks != expected_ticks:
        problems.append(f"ticks {ticks} != expected {expected_ticks}")
    jpy = s.get("jpy_balance")
    if not s.get("is_complete") or jpy is None or jpy <= 0:
        problems.append(f"final state: complete={s.get('is_complete')} jpy_balance={jpy}")
    return {"scenario": name, "ok": not problems, "session": sid, "ticks": ticks,
            "missing_rate_ticks": missing_rate_ticks, "jpy": jpy,
            "secs": round(time.time() - t0, 1), "problems": problems}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("user_id")
    ap.add_argument("base_url", nargs="?", default="http://34.146.231.219:8000")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", help="comma-separated scenario names")
    ap.add_argument("--currencies", help="comma-separated foreign currencies to trade/check (default: all 13)")
    a = ap.parse_args()
    foreign = a.currencies.split(",") if a.currencies else ALL_FOREIGN
    if a.only:
        names = a.only.split(",")
    else:
        names = [r["name"] for r in csv.DictReader(open(DATA_DIR / "scenarios.csv"))]
    print(f"{len(names)} scenarios, user={a.user_id}, workers={a.workers}, server={a.base_url}", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_one, n, a.user_id, a.base_url, foreign): n for n in names}
        for f in as_completed(futs):
            res = f.result()
            results.append(res)
            mark = "OK " if res["ok"] else "NG "
            print(f"{mark} {res['scenario']:<12} ticks={res.get('ticks', '-'):<5} "
                  f"jpy={res.get('jpy', '-')!s:<16} {res.get('secs', '-')}s "
                  f"{'; '.join(res.get('problems', [])) or res.get('error', '')}", flush=True)
    bad = [r for r in results if not r["ok"]]
    print(f"\n{len(results) - len(bad)}/{len(results)} scenarios OK")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
