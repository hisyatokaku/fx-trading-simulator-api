"""Trader service for managing traders."""

from typing import List

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trader import Trader
from app.schemas.trader import TraderEntry


class TraderService:
    """Service for trader operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_upsert(self, entries: List[TraderEntry]) -> tuple[int, int]:
        """Bulk insert or update traders.

        Returns tuple of (inserted_count, updated_count).
        """
        if not entries:
            return 0, 0

        inserted = 0
        updated = 0

        for entry in entries:
            existing = await self.db.execute(
                select(Trader).where(Trader.user_id == entry.user_id)
            )
            if existing.scalar_one_or_none():
                updated += 1
            else:
                inserted += 1

            stmt = insert(Trader).values(
                user_id=entry.user_id,
                type=entry.type,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id"],
                set_={"type": entry.type},
            )
            await self.db.execute(stmt)

        await self.db.flush()
        return inserted, updated
