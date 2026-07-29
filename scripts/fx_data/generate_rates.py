#!/usr/bin/env python3
"""CLI: download 1-minute FX data from HistData.com and convert it into a
JPY-cross-rate CSV usable by the trading simulator API.

Example (matches the GameConfig scenario Feb_Apr_2019_without_commission):

    python generate_rates.py --start 2019-02-01 --end 2019-04-28 \\
        --out ../../sample/rates_1min_generated.csv
"""
import argparse
import datetime
import logging
import sys
from pathlib import Path

from convert_to_jpy_rates import OUTPUT_CURRENCIES, build_rates, write_sample_format_csv

DEFAULT_RATES_CSV = Path(__file__).resolve().parents[2] / "src/main/resources/data/rates.csv"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", required=True, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date, YYYY-MM-DD (inclusive)")
    parser.add_argument("--out", required=True, type=Path, help="Output CSV path")
    parser.add_argument("--cache-dir", type=Path, default=Path(__file__).parent / "cache",
                         help="Where downloaded HistData.com ZIPs are cached (default: ./cache)")
    parser.add_argument("--rates-csv", type=Path, default=DEFAULT_RATES_CSV,
                         help="Existing daily rates.csv used as fallback for currencies "
                              "HistData.com doesn't carry (default: repo's data/rates.csv)")
    parser.add_argument("--currencies", default=",".join(OUTPUT_CURRENCIES),
                         help="Comma-separated currency list to generate (default: all 24)")
    parser.add_argument("--yes", action="store_true",
                         help="Skip the confirmation prompt before hitting HistData.com")
    return parser.parse_args(argv)


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)

    start_date = datetime.date.fromisoformat(args.start)
    end_date = datetime.date.fromisoformat(args.end)
    currencies = [c.strip().upper() for c in args.currencies.split(",") if c.strip()]

    calendar_days = (end_date - start_date).days + 1
    print("=" * 60)
    print(f"Range        : {start_date} to {end_date} ({calendar_days} calendar days)")
    print(f"Currencies   : {', '.join(currencies)}")
    print(f"Cache dir    : {args.cache_dir}")
    print(f"Fallback CSV : {args.rates_csv}")
    print(f"Output       : {args.out}")
    print(f"Est. rows    : up to ~{calendar_days * 1440:,} (fewer in practice - weekends "
          f"have no forex trading and this is 24/5 market data, not a fixed grid)")
    print("This will make real network requests to HistData.com for any pairs not")
    print("already cached locally.")
    print("=" * 60)

    if not args.yes:
        answer = input("Proceed? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1

    df = build_rates(start_date, end_date, args.cache_dir, args.rates_csv, currencies)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_sample_format_csv(df, args.out)
    print(f"Wrote {len(df):,} rows to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
