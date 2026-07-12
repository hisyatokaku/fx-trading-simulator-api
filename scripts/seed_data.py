#!/usr/bin/env python
"""Upsert traders.csv and rates.csv into a running instance via its API.

Safe to run repeatedly: existing rows are updated in place (by user_id
for traders, by currency+timestamp for rates) via the /api/trader/bulk
and /api/rate/bulk endpoints. New rows are inserted; rows no longer
present in the CSVs are left untouched.

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
CURRENCIES = ["USD", "EUR", "GBP", "AUD", "CHF", "CNY", "HKD"]


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
                rate_value = row.get(currency)
                if rate_value:
                    rates.append({
                        "currency": currency,
                        "timestamp": timestamp.isoformat(),
                        "rate_to_jpy": rate_value.strip(),
                    })
    return rates


def main():
    base_url = (sys.argv[1] if len(sys.argv) > 1 else None) or os.getenv("API_BASE_URL", "http://localhost:8000")

    traders = load_traders(DATA_DIR / "traders.csv")
    rates = load_rates(DATA_DIR / "rates.csv")

    with httpx.Client(base_url=base_url, timeout=60.0) as client:
        if traders:
            resp = client.post("/api/trader/bulk", json={"traders": traders})
            resp.raise_for_status()
            result = resp.json()
            print(f"Traders: {result['inserted']} inserted, {result['updated']} updated.")

        if rates:
            # Chunk to keep request payloads reasonable.
            chunk_size = 500
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
