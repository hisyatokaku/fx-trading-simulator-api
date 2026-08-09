#!/usr/bin/env python
"""Generate realistic FX rate data (daily, hourly, 5-min) for 2016."""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

CURRENCIES = ["USD", "EUR", "GBP", "AUD", "CHF", "CNY", "HKD"]

# Starting rates (JPY per 1 unit of currency)
BASE_RATES = {
    "USD": 118.25,
    "EUR": 128.50,
    "GBP": 173.25,
    "AUD": 85.50,
    "CHF": 118.00,
    "CNY": 18.05,
    "HKD": 15.25,
}

# Daily volatility (std dev as fraction of rate)
DAILY_VOL = {
    "USD": 0.003,
    "EUR": 0.004,
    "GBP": 0.005,
    "AUD": 0.005,
    "CHF": 0.004,
    "CNY": 0.001,
    "HKD": 0.001,
}


def random_walk(rate: float, vol: float) -> float:
    """Apply one random walk step."""
    change = random.gauss(0, vol * rate)
    return round(rate + change, 2)


def generate_daily_rates(start: datetime, end: datetime) -> list[tuple[datetime, dict]]:
    """Generate daily rates for all trading days (Mon-Fri) in range."""
    rows = []
    rates = dict(BASE_RATES)
    current = start

    while current <= end:
        if current.weekday() < 5:  # Mon-Fri
            rows.append((current, dict(rates)))
            # Evolve for next day
            for ccy in CURRENCIES:
                rates[ccy] = random_walk(rates[ccy], DAILY_VOL[ccy])
        current += timedelta(days=1)

    return rows


def generate_intraday_rates(
    date: datetime, rates_at_open: dict, interval_minutes: int
) -> list[tuple[datetime, dict]]:
    """Generate intra-day rates at given interval from 09:00 to 17:00."""
    rows = []
    # Use proportionally smaller volatility per step
    steps_per_day = (8 * 60) // interval_minutes
    step_vol = {ccy: DAILY_VOL[ccy] / (steps_per_day ** 0.5) for ccy in CURRENCIES}

    rates = dict(rates_at_open)
    ts = date.replace(hour=9, minute=0, second=0)
    end_ts = date.replace(hour=17, minute=0, second=0)

    while ts <= end_ts:
        rows.append((ts, dict(rates)))
        ts += timedelta(minutes=interval_minutes)
        for ccy in CURRENCIES:
            rates[ccy] = random_walk(rates[ccy], step_vol[ccy])

    return rows


def main():
    out_path = Path(__file__).parent.parent / "data" / "rates.csv"

    # 1. Generate daily rates for all of 2016
    daily = generate_daily_rates(datetime(2016, 1, 4), datetime(2016, 12, 30))

    # Build a lookup: date -> rates (for seeding intra-day data)
    daily_lookup = {row[0].date(): row[1] for row in daily}

    # 2. Generate hourly rates for Jan 4–8 (DEMO_2016_HOURLY range)
    hourly = []
    for d in [4, 5, 6, 7, 8]:
        date = datetime(2016, 1, d)
        if date.weekday() < 5:
            open_rates = daily_lookup.get(date.date(), BASE_RATES)
            hourly += generate_intraday_rates(date, open_rates, interval_minutes=60)

    # 3. Generate 5-min rates for Jan 4 (DEMO_5MIN range)
    five_min = generate_intraday_rates(
        datetime(2016, 1, 4), daily_lookup[datetime(2016, 1, 4).date()], interval_minutes=5
    )

    # Merge all rows, deduplicate by timestamp (intra-day takes priority over daily midnight)
    all_rows: dict[datetime, dict] = {}
    for ts, rates in daily:
        all_rows[ts] = rates
    for ts, rates in hourly:
        all_rows[ts] = rates
    for ts, rates in five_min:
        all_rows[ts] = rates

    sorted_rows = sorted(all_rows.items())

    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["datetime"] + CURRENCIES)
        for ts, rates in sorted_rows:
            writer.writerow([ts.strftime("%Y-%m-%d %H:%M:%S")] + [rates[c] for c in CURRENCIES])

    print(f"Written {len(sorted_rows)} rows to {out_path}")

    # Summary
    daily_count = sum(1 for ts, _ in sorted_rows if ts.hour == 0 and ts.minute == 0)
    intra_count = len(sorted_rows) - daily_count
    print(f"  Daily rows (midnight): {daily_count}")
    print(f"  Intra-day rows:        {intra_count}")


if __name__ == "__main__":
    main()
