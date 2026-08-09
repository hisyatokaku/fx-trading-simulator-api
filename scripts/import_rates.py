#!/usr/bin/env python
"""Import exchange rates from a CSV file."""

import argparse
import asyncio
import csv
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal, async_engine, Base
from app.models import Rate


async def import_rates(csv_path: str, date_format: str = "%Y-%m-%d"):
    """Import rates from CSV file.

    Expected CSV format:
    date,USD,EUR,GBP,AUD,CHF,CNY,HKD
    2016-01-04,118.25,128.75,173.50,85.50,118.00,18.05,15.25
    """
    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        return

    # Create tables if needed
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    rates_inserted = 0
    rates_updated = 0
    errors = []

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        if not headers:
            print("Error: CSV file has no headers")
            return

        # Find date column (case-insensitive)
        date_col = None
        for h in headers:
            if h.lower() == "date":
                date_col = h
                break

        if not date_col:
            print("Error: No 'date' column found in CSV")
            return

        # Currency columns are everything except date
        currency_cols = [h for h in headers if h.lower() != "date"]
        print(f"Found currencies: {currency_cols}")

        async with AsyncSessionLocal() as session:
            for row_num, row in enumerate(reader, start=2):
                try:
                    date_str = row.get(date_col, "").strip()
                    if not date_str:
                        continue

                    timestamp = datetime.strptime(date_str, date_format)

                    for currency in currency_cols:
                        rate_str = row.get(currency, "").strip()
                        if not rate_str:
                            continue

                        rate_value = Decimal(rate_str)

                        # Check if exists
                        result = await session.execute(
                            select(Rate).where(
                                Rate.currency == currency,
                                Rate.timestamp == timestamp
                            )
                        )
                        existing = result.scalar_one_or_none()

                        if existing:
                            existing.rate_to_jpy = rate_value
                            rates_updated += 1
                        else:
                            rate = Rate(
                                currency=currency,
                                timestamp=timestamp,
                                rate_to_jpy=rate_value,
                            )
                            session.add(rate)
                            rates_inserted += 1

                except Exception as e:
                    errors.append(f"Row {row_num}: {e}")
                    if len(errors) > 100:
                        print("Too many errors, stopping...")
                        break

                # Commit in batches
                if (rates_inserted + rates_updated) % 500 == 0:
                    await session.commit()
                    print(f"Processed {rates_inserted + rates_updated} rates...")

            await session.commit()

    print(f"\nImport complete:")
    print(f"  Inserted: {rates_inserted}")
    print(f"  Updated: {rates_updated}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for error in errors[:10]:
            print(f"    - {error}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more")


def main():
    parser = argparse.ArgumentParser(description="Import exchange rates from CSV")
    parser.add_argument("csv_file", help="Path to CSV file")
    parser.add_argument(
        "--date-format",
        default="%Y-%m-%d",
        help="Date format in CSV (default: %%Y-%%m-%%d)"
    )

    args = parser.parse_args()
    asyncio.run(import_rates(args.csv_file, args.date_format))


if __name__ == "__main__":
    main()
