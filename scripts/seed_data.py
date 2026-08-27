#!/usr/bin/env python
"""Upsert scenarios.csv, traders.csv, and rates.csv into a running instance via its API.

Safe to run repeatedly: existing rows are updated in place (by name for
scenarios, user_id for traders, currency+timestamp for rates) via the
/api/scenario/bulk, /api/trader/bulk, and /api/rate/bulk endpoints. New
rows are inserted; rows no longer present in the CSVs are left untouched.

Usage:
    python scripts/seed_data.py [base_url]

base_url defaults to $API_BASE_URL or http://localhost:8000.
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent.parent / "data"
CURRENCIES = [
    "USD", "EUR", "GBP", "AUD", "NZD", "CAD", "CHF",
    "TRY", "ZAR", "MXN", "NOK", "SEK", "HKD",
]


def load_scenarios(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []

    scenarios = []
    with open(csv_path, "r") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            if not name:
                continue

            start_str = (row.get("start_datetime") or "").strip()
            end_str = (row.get("end_datetime") or "").strip()
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            scenarios.append({
                "name": name,
                "start_datetime": start_dt.isoformat(),
                "end_datetime": end_dt.isoformat(),
                "time_interval_seconds": int(row.get("time_interval_seconds") or 86400),
                "game_type": (row.get("game_type") or "ANY").strip(),
                "initial_balance": float(row.get("initial_balance") or 1000000.0),
            })
    return scenarios


def load_traders(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []

    traders = []
    with open(csv_path, "r") as f:
        for row in csv.DictReader(f):
            user_id = row.get("user_id") or row.get("userId")
            if not user_id:
                continue
            traders.append({"user_id": user_id.strip(), "type": (row.get("type") or "test").strip()})
    return traders


def load_rates(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []

    rates = []
    with open(csv_path, "r") as f:
        for row in csv.DictReader(f):
            date_str = (row.get("datetime") or row.get("date") or row.get("Date") or "").strip()
            if not date_str:
                continue

            timestamp = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    timestamp = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            if timestamp is None:
                continue

            for currency in CURRENCIES:
                rate_value = (row.get(currency) or "").strip()
                if not rate_value:
                    continue
                try:
                    if float(rate_value) <= 0:
                        continue  # 0 = dummy placeholder (e.g. an unused currency in a
                                  # synthetic scenario), not a real rate; the API requires > 0
                except ValueError:
                    continue
                rates.append({
                    "currency": currency,
                    "timestamp": timestamp.isoformat(),
                    "rate_to_jpy": rate_value,
                })
    return rates


def main():
    base_url = (sys.argv[1] if len(sys.argv) > 1 else None) or os.getenv("API_BASE_URL", "http://localhost:8000")

    scenarios = load_scenarios(DATA_DIR / "scenarios.csv")
    traders = load_traders(DATA_DIR / "traders.csv")
    rates = load_rates(DATA_DIR / "rates.csv")

    with httpx.Client(base_url=base_url, timeout=60.0) as client:
        if scenarios:
            resp = client.post("/api/scenario/bulk", json={"scenarios": scenarios})
            resp.raise_for_status()
            result = resp.json()
            print(f"Scenarios: {result['inserted']} inserted, {result['updated']} updated.")

        if traders:
            resp = client.post("/api/trader/bulk", json={"traders": traders})
            resp.raise_for_status()
            result = resp.json()
            print(f"Traders: {result['inserted']} inserted, {result['updated']} updated.")

        if rates:
            # Chunk to keep request payloads reasonable.
            chunk_size = 5000
            total_inserted = total_updated = 0
            for i in range(0, len(rates), chunk_size):
                chunk = rates[i:i + chunk_size]
                resp = client.post("/api/rate/bulk", json={"rates": chunk})
                resp.raise_for_status()
                result = resp.json()
                total_inserted += result["inserted"]
                total_updated += result["updated"]
            print(f"Rates: {total_inserted} inserted, {total_updated} updated.")


if __name__ == "__main__":
    main()
