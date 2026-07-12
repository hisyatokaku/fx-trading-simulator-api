#!/usr/bin/env python
"""Initialize the database with sample data."""

import asyncio
import csv
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal, async_engine, Base
from app.models import Scenario, Trader, Rate


async def create_tables():
    """Create all database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully.")


async def create_default_scenarios():
    """Create default trading scenarios."""
    scenarios = [
        {
            "name": "DEMO_2016",
            "start_datetime": datetime(2016, 1, 4),
            "end_datetime": datetime(2016, 12, 30),
            "time_interval_seconds": 86400,  # 1 day
            "game_type": "ANY",
            "initial_balance": 1000000,
        },
        {
            "name": "DEMO_2016_HOURLY",
            "start_datetime": datetime(2016, 1, 4, 9, 0, 0),
            "end_datetime": datetime(2016, 1, 8, 17, 0, 0),
            "time_interval_seconds": 3600,  # 1 hour
            "game_type": "ANY",
            "initial_balance": 1000000,
        },
        {
            "name": "DEMO_5MIN",
            "start_datetime": datetime(2016, 1, 4, 9, 0, 0),
            "end_datetime": datetime(2016, 1, 4, 17, 0, 0),
            "time_interval_seconds": 300,  # 5 minutes
            "game_type": "ANY",
            "initial_balance": 1000000,
        },
    ]

    async with AsyncSessionLocal() as session:
        for scenario_data in scenarios:
            # Check if exists
            result = await session.execute(
                select(Scenario).where(Scenario.name == scenario_data["name"])
            )
            existing = result.scalar_one_or_none()

            if not existing:
                scenario = Scenario(**scenario_data)
                session.add(scenario)
                print(f"Created scenario: {scenario_data['name']}")
            else:
                print(f"Scenario already exists: {scenario_data['name']}")

        await session.commit()


async def import_rates_from_csv(csv_path: str):
    """Import exchange rates from CSV file."""
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return

    rates_to_insert = []

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse date from CSV (assuming format like "2016-01-04")
            try:
                date_str = row.get("datetime") or row.get("date") or row.get("Date")
                if not date_str:
                    continue

                date_str = date_str.strip()
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        timestamp = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError(f"Unrecognised date format: {date_str}")

                # Get currency rates (columns like USD, EUR, etc.)
                for currency in ["USD", "EUR", "GBP", "AUD", "CHF", "CNY", "HKD"]:
                    rate_value = row.get(currency)
                    if rate_value:
                        rate = float(rate_value.strip())
                        rates_to_insert.append({
                            "currency": currency,
                            "timestamp": timestamp,
                            "rate_to_jpy": rate,
                        })
            except Exception as e:
                print(f"Error parsing row: {row}, error: {e}")
                continue

    if not rates_to_insert:
        print("No rates found to import.")
        return

    async with AsyncSessionLocal() as session:
        for rate_data in rates_to_insert:
            # Check if exists
            result = await session.execute(
                select(Rate).where(
                    Rate.currency == rate_data["currency"],
                    Rate.timestamp == rate_data["timestamp"]
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                rate = Rate(**rate_data)
                session.add(rate)

        await session.commit()
        print(f"Imported {len(rates_to_insert)} rate records.")


async def import_traders_from_csv(csv_path: str):
    """Import traders from CSV file."""
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return

    async with AsyncSessionLocal() as session:
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                user_id = row.get("user_id") or row.get("userId")
                trader_type = row.get("type", "test")

                if not user_id:
                    continue

                # Check if exists
                result = await session.execute(
                    select(Trader).where(Trader.user_id == user_id)
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    trader = Trader(user_id=user_id, type=trader_type)
                    session.add(trader)
                    count += 1

        await session.commit()
        print(f"Imported {count} traders.")


async def main():
    """Main initialization function."""
    print("Initializing database...")

    # Create tables
    await create_tables()

    # Create default scenarios
    await create_default_scenarios()

    # Import data from CSV files
    data_dir = Path(__file__).parent.parent / "data"

    rates_csv = data_dir / "rates.csv"
    if rates_csv.exists():
        await import_rates_from_csv(str(rates_csv))

    traders_csv = data_dir / "traders.csv"
    if traders_csv.exists():
        await import_traders_from_csv(str(traders_csv))

    print("Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
