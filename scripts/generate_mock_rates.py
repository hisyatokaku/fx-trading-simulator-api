#!/usr/bin/env python
"""Generate mock exchange rates for testing sub-day intervals."""

import asyncio
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal, async_engine, Base
from app.models import Rate


# Base rates (approximate JPY values)
BASE_RATES = {
    "USD": Decimal("115.0"),
    "EUR": Decimal("125.0"),
    "GBP": Decimal("155.0"),
    "AUD": Decimal("85.0"),
    "CHF": Decimal("115.0"),
    "CNY": Decimal("17.5"),
    "HKD": Decimal("14.8"),
}


def generate_rate_with_volatility(base_rate: Decimal, volatility: float = 0.001) -> Decimal:
    """Generate a rate with random volatility."""
    change = Decimal(str(random.uniform(-volatility, volatility)))
    new_rate = base_rate * (1 + change)
    return new_rate.quantize(Decimal("0.0001"))


async def generate_minute_rates(
    start: datetime,
    end: datetime,
    interval_minutes: int = 5
):
    """Generate mock rates at specified minute intervals."""
    print(f"Generating rates from {start} to {end} at {interval_minutes}-minute intervals...")

    current = start
    rates_generated = 0
    current_rates = BASE_RATES.copy()

    async with AsyncSessionLocal() as session:
        while current <= end:
            for currency, base_rate in current_rates.items():
                # Check if rate already exists
                result = await session.execute(
                    select(Rate).where(
                        Rate.currency == currency,
                        Rate.timestamp == current
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    # Generate new rate with slight volatility
                    new_rate = generate_rate_with_volatility(base_rate)
                    current_rates[currency] = new_rate

                    rate = Rate(
                        currency=currency,
                        timestamp=current,
                        rate_to_jpy=new_rate,
                    )
                    session.add(rate)
                    rates_generated += 1

            current += timedelta(minutes=interval_minutes)

            # Commit in batches
            if rates_generated > 0 and rates_generated % 1000 == 0:
                await session.commit()
                print(f"Generated {rates_generated} rates...")

        await session.commit()

    print(f"Generated {rates_generated} total rates.")


async def generate_hourly_rates(start: datetime, end: datetime):
    """Generate mock rates at hourly intervals."""
    await generate_minute_rates(start, end, interval_minutes=60)


async def generate_daily_rates(start: datetime, end: datetime):
    """Generate mock rates at daily intervals."""
    print(f"Generating daily rates from {start} to {end}...")

    current = start
    rates_generated = 0
    current_rates = BASE_RATES.copy()

    async with AsyncSessionLocal() as session:
        while current <= end:
            for currency, base_rate in current_rates.items():
                # Check if rate already exists
                result = await session.execute(
                    select(Rate).where(
                        Rate.currency == currency,
                        Rate.timestamp == current
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    # Generate new rate with slightly higher daily volatility
                    new_rate = generate_rate_with_volatility(base_rate, volatility=0.005)
                    current_rates[currency] = new_rate

                    rate = Rate(
                        currency=currency,
                        timestamp=current,
                        rate_to_jpy=new_rate,
                    )
                    session.add(rate)
                    rates_generated += 1

            current += timedelta(days=1)

        await session.commit()

    print(f"Generated {rates_generated} daily rates.")


async def main():
    """Main function to generate mock rates."""
    # Create tables if needed
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Generate 5-minute rates for one week
    start_5min = datetime(2016, 1, 4, 9, 0, 0)
    end_5min = datetime(2016, 1, 8, 17, 0, 0)
    await generate_minute_rates(start_5min, end_5min, interval_minutes=5)

    # Generate hourly rates for one month
    start_hourly = datetime(2016, 1, 4, 0, 0, 0)
    end_hourly = datetime(2016, 1, 31, 23, 0, 0)
    await generate_hourly_rates(start_hourly, end_hourly)

    # Generate daily rates for one year
    start_daily = datetime(2016, 1, 4)
    end_daily = datetime(2016, 12, 30)
    await generate_daily_rates(start_daily, end_daily)

    print("Mock rate generation complete!")


if __name__ == "__main__":
    asyncio.run(main())
