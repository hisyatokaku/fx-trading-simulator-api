"""Rate service for managing exchange rates."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rate import Rate
from app.schemas.rate import RateEntry
from app.utils.rate_matrix import RateMatrix


class RateService:
    """Service for rate operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_rates_at_timestamp(self, timestamp: datetime) -> Dict[str, Decimal]:
        """Get all exchange rates at an exact timestamp.

        Raises RuntimeError if no rates exist for the given timestamp.
        """
        result = await self.db.execute(
            select(Rate).where(Rate.timestamp == timestamp)
        )
        rows = result.scalars().all()

        if not rows:
            raise RuntimeError(f"Rates not found for timestamp: {timestamp}")

        return {row.currency: row.rate_to_jpy for row in rows}

    async def get_rate_matrix(self, timestamp: datetime) -> RateMatrix:
        """Get a RateMatrix for currency conversions at a timestamp."""
        rates = await self.get_rates_at_timestamp(timestamp)
        return RateMatrix(rates)

    async def bulk_upsert(self, entries: List[RateEntry]) -> tuple[int, int]:
        """Bulk insert or update rates.

        Returns tuple of (inserted_count, updated_count).
        """
        if not entries:
            return 0, 0

        # Last occurrence wins, so one statement never touches the same row
        # twice -- PostgreSQL rejects that in ON CONFLICT DO UPDATE.
        deduped = {(e.currency, e.timestamp): e for e in entries}

        result = await self.db.execute(
            select(Rate.currency, Rate.timestamp).where(and_(
                Rate.currency.in_({currency for currency, _ in deduped}),
                Rate.timestamp.in_({timestamp for _, timestamp in deduped}),
            ))
        )
        existing = {(row.currency, row.timestamp) for row in result.fetchall()}

        updated = sum(1 for key in deduped if key in existing)
        inserted = len(deduped) - updated

        stmt = insert(Rate).values([
            {
                "currency": entry.currency,
                "timestamp": entry.timestamp,
                "rate_to_jpy": entry.rate_to_jpy,
            }
            for entry in deduped.values()
        ])
        stmt = stmt.on_conflict_do_update(
            constraint="uq_rate_currency_timestamp",
            set_={"rate_to_jpy": stmt.excluded.rate_to_jpy},
        )
        await self.db.execute(stmt)

        await self.db.flush()
        return inserted, updated

    async def check_coverage(
        self,
        timestamps: List[datetime],
        currencies: List[str],
    ) -> Dict[str, List[datetime]]:
        """Check which (currency, timestamp) pairs are missing from the rates table.

        Returns a dict of currency -> list of missing timestamps.
        Fetches all existing pairs in a single query.
        """
        if not timestamps or not currencies:
            return {c: [] for c in currencies}

        result = await self.db.execute(
            select(Rate.currency, Rate.timestamp)
            .where(and_(
                Rate.currency.in_(currencies),
                Rate.timestamp.in_(timestamps),
            ))
        )
        existing = {(row.currency, row.timestamp) for row in result.fetchall()}

        missing: Dict[str, List[datetime]] = {}
        for currency in currencies:
            missing_ts = [ts for ts in timestamps if (currency, ts) not in existing]
            missing[currency] = sorted(missing_ts)

        return missing

    async def get_available_timestamps(
        self,
        start: datetime,
        end: datetime,
        currency: str = None
    ) -> List[datetime]:
        """Get all available timestamps in a range."""
        query = select(Rate.timestamp).distinct()

        if currency:
            query = query.where(Rate.currency == currency)

        query = query.where(and_(
            Rate.timestamp >= start,
            Rate.timestamp <= end
        )).order_by(Rate.timestamp)

        result = await self.db.execute(query)
        return [row[0] for row in result.fetchall()]
