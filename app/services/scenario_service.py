"""Scenario service for managing trading scenarios."""

from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate


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
