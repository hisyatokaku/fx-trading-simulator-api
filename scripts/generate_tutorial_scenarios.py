#!/usr/bin/env python
"""Generate synthetic USD/JPY price series for the tutorial's TUTORIAL1/2/3 scenarios.

Reproduces the exact generation rules used to teach notebooks/tutorial_private.ipynb's
challenge 1/2/3 (same formulas, same seed=42), then:

  1. Writes each series as a standalone rates-format CSV: data/day1_scenario{1,2,3}.csv
     (same columns as data/rates.csv; USD holds the generated series, every other
     currency is filled with 0 as a dummy value).
  2. Merges those rows into data/rates.csv (de-duped by datetime, so reruns don't
     duplicate rows).
  3. Upserts a TUTORIAL{1,2,3} row into data/scenarios.csv with a far-past date range
     that can't collide with real rate data.

This only edits the data/ CSVs. Run `python scripts/seed_data.py` afterward to push
the merged CSVs into a running instance's DB.

Requires numpy (not an app dependency): pip install numpy

Usage:
    python scripts/generate_tutorial_scenarios.py
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data"
RATES_CSV = DATA_DIR / "rates.csv"
SCENARIOS_CSV = DATA_DIR / "scenarios.csv"

N_TICKS = 1000
INTERVAL_SECONDS = 60
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"

# far in the past relative to data/rates.csv's real data (starts 2026-06-01),
# each non-overlapping so TUTORIAL1/2/3 can never collide with each other.
SCENARIO_STARTS = {
    1: datetime(2020, 1, 6, 0, 0, 0),
    2: datetime(2020, 2, 3, 0, 0, 0),
    3: datetime(2020, 3, 2, 0, 0, 0),
}


def generate_scenario1(n_ticks: int = N_TICKS, start_price: float = 150.0,
                        up_prob: float = 0.61, up_mean: float = 0.0086,
                        down_mean: float = 0.0032, noise_std: float = 0.09,
                        seed: int = 42) -> np.ndarray:
    """Biased random walk — 'ゆっくり育つマーケット' (same rule as notebook Part 3.1)."""
    rng = np.random.RandomState(seed)
    p = np.zeros(n_ticks)
    p[0] = start_price
    for t in range(1, n_ticks):
        if rng.rand() < up_prob:
            d = abs(rng.normal(up_mean, noise_std))
        else:
            d = -abs(rng.normal(down_mean, noise_std))
        p[t] = p[t - 1] + d
    return np.round(p, 3)


def generate_scenario2(n_ticks: int = N_TICKS, start_price: float = 150.0,
                        mean_price: float = 150.0, theta: float = 0.1,
                        sigma: float = 1.1, seed: int = 42) -> np.ndarray:
    """Mean-reverting OU process — '引き戻されるマーケット' (notebook Part 4.1)."""
    rng = np.random.RandomState(seed)
    p = np.zeros(n_ticks)
    p[0] = start_price
    for t in range(1, n_ticks):
        p[t] = (p[t - 1]
                + theta * (mean_price - p[t - 1])
                + sigma * rng.normal())
    return np.round(p, 3)


def generate_scenario3(n_ticks: int = N_TICKS, start_price: float = 150.0,
                        extra_length_avg: int = 10, min_regime_length: int = 40,
                        drift_strength: float = 0.06, volatility: float = 0.24,
                        seed: int = 42) -> np.ndarray:
    """Hidden-regime trending process — 'トレンドが続くマーケット' (notebook Part 5.1)."""
    rng = np.random.RandomState(seed)
    p = np.zeros(n_ticks)
    p[0] = start_price
    regime, run_len = 1, 0
    p_switch = 1.0 / extra_length_avg
    for t in range(1, n_ticks):
        if rng.rand() < p_switch and run_len > min_regime_length:
            regime *= -1
            run_len = 0
        else:
            run_len += 1
        p[t] = (p[t - 1]
                + regime * drift_strength
                + volatility * rng.normal())
    return np.round(p, 3)


GENERATORS = {1: generate_scenario1, 2: generate_scenario2, 3: generate_scenario3}


def read_rates_header(csv_path: Path) -> list[str]:
    with open(csv_path, "r", newline="") as f:
        return next(csv.reader(f))


def build_scenario_rows(n: int, currencies: list[str]) -> list[dict]:
    prices = GENERATORS[n]()
    start = SCENARIO_STARTS[n]
    rows = []
    for i, price in enumerate(prices):
        dt = start + timedelta(seconds=INTERVAL_SECONDS * i)
        row = {"datetime": dt.strftime(DATETIME_FMT)}
        for currency in currencies:
            row[currency] = f"{price:.4f}" if currency == "USD" else "0.0000"
        rows.append(row)
    return rows


def write_day1_csv(n: int, header: list[str], rows: list[dict]) -> Path:
    out_path = DATA_DIR / f"day1_scenario{n}.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def merge_into_rates_csv(header: list[str], all_new_rows: list[dict]) -> tuple[int, int]:
    existing_rows = []
    if RATES_CSV.exists():
        with open(RATES_CSV, "r", newline="") as f:
            existing_rows = list(csv.DictReader(f))

    new_datetimes = {row["datetime"] for row in all_new_rows}
    kept = [row for row in existing_rows if row["datetime"] not in new_datetimes]
    removed = len(existing_rows) - len(kept)

    merged = kept + all_new_rows
    merged.sort(key=lambda row: row["datetime"])

    with open(RATES_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(merged)

    return len(all_new_rows), removed


def upsert_scenarios_csv() -> None:
    fieldnames = ["name", "start_datetime", "end_datetime",
                  "time_interval_seconds", "game_type", "initial_balance"]

    existing_rows = []
    if SCENARIOS_CSV.exists():
        with open(SCENARIOS_CSV, "r", newline="") as f:
            existing_rows = list(csv.DictReader(f))

    tutorial_names = {f"TUTORIAL{n}" for n in SCENARIO_STARTS}
    kept = [row for row in existing_rows if row["name"] not in tutorial_names]

    new_rows = []
    for n, start in SCENARIO_STARTS.items():
        end = start + timedelta(seconds=INTERVAL_SECONDS * (N_TICKS - 1))
        new_rows.append({
            "name": f"TUTORIAL{n}",
            "start_datetime": start.strftime(DATETIME_FMT),
            "end_datetime": end.strftime(DATETIME_FMT),
            "time_interval_seconds": INTERVAL_SECONDS,
            "game_type": "ANY",
            "initial_balance": 1000000,
        })

    with open(SCENARIOS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(kept + new_rows)


def main():
    currencies = read_rates_header(RATES_CSV)[1:]  # drop "datetime"

    all_new_rows = []
    for n in sorted(GENERATORS):
        rows = build_scenario_rows(n, currencies)
        out_path = write_day1_csv(n, read_rates_header(RATES_CSV), rows)
        print(f"TUTORIAL{n}: wrote {len(rows)} rows -> {out_path}")
        all_new_rows.extend(rows)

    inserted, replaced = merge_into_rates_csv(read_rates_header(RATES_CSV), all_new_rows)
    print(f"data/rates.csv: merged {inserted} rows ({replaced} replaced from a prior run)")

    upsert_scenarios_csv()
    print(f"data/scenarios.csv: upserted TUTORIAL1/2/3")
    print("\nNext: run `python scripts/seed_data.py` to push these into a running instance's DB.")


if __name__ == "__main__":
    main()
