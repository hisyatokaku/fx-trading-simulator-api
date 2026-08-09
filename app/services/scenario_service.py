"""Scenario service for managing trading scenarios."""

from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioEntry, ScenarioUpdate


class ScenarioService:
    """Service for scenario CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ScenarioCreate) -> Scenario:
        """Create a new scenario."""
        scenario = Scenario(
            name=data.name,
            start_datetime=data.start_datetime,
            end_datetime=data.end_datetime,
            time_interval_seconds=data.time_interval_seconds,
            game_type=data.game_type,
            initial_balance=data.initial_balance,
        )
        self.db.add(scenario)
        await self.db.flush()
        await self.db.refresh(scenario)
        return scenario

    async def bulk_upsert(self, entries: List[ScenarioEntry]) -> tuple[int, int]:
        """Bulk insert or update scenarios, keyed by name.

        Returns tuple of (inserted_count, updated_count).
        """
        if not entries:
            return 0, 0

        inserted = 0
        updated = 0

        for entry in entries:
            existing = await self.get_by_name(entry.name)
            if existing:
                updated += 1
            else:
                inserted += 1

            values = {
                "name": entry.name,
                "start_datetime": entry.start_datetime,
                "end_datetime": entry.end_datetime,
                "time_interval_seconds": entry.time_interval_seconds,
                "game_type": entry.game_type,
                "initial_balance": entry.initial_balance,
            }
            stmt = insert(Scenario).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["name"],
                set_={k: v for k, v in values.items() if k != "name"},
            )
            await self.db.execute(stmt)

        await self.db.flush()
        return inserted, updated

    async def get_by_name(self, name: str) -> Optional[Scenario]:
        """Get a scenario by name."""
        result = await self.db.execute(
            select(Scenario).where(Scenario.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, scenario_id: int) -> Optional[Scenario]:
        """Get a scenario by ID."""
        result = await self.db.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Scenario]:
        """Get all scenarios."""
        result = await self.db.execute(
            select(Scenario).order_by(Scenario.name)
        )
        return list(result.scalars().all())

    async def update(self, name: str, data: ScenarioUpdate) -> Optional[Scenario]:
        """Update a scenario by name."""
        scenario = await self.get_by_name(name)
        if not scenario:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(scenario, field, value)

        await self.db.flush()
        await self.db.refresh(scenario)
        return scenario

    async def delete(self, name: str) -> bool:
        """Delete a scenario by name."""
        scenario = await self.get_by_name(name)
        if not scenario:
            return False

        await self.db.delete(scenario)
        await self.db.flush()
        return True
