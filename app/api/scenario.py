"""Scenario API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    ScenarioBulkUpload,
    ScenarioBulkResponse,
    RateCheckRequest,
    RateCheckResponse,
    ScenarioRatesResponse,
)
from app.services.scenario_service import ScenarioService
from app.services.rate_service import RateService
from app.utils.date_utils import add_interval

router = APIRouter()


def _scenario_timestamps(scenario) -> list:
    """Generate the timestamps visited by a scenario."""
    timestamps = []
    current = scenario.start_datetime
    while current <= scenario.end_datetime:
        timestamps.append(current)
        current = add_interval(current, scenario.time_interval_seconds)
    return timestamps


@router.get("/", response_model=List[ScenarioResponse])
async def list_scenarios(db: AsyncSession = Depends(get_db)):
    """List all scenarios, except evaluation ones (names containing EVAL)."""
    service = ScenarioService(db)
    scenarios = await service.get_all()
    # Evaluation scenarios are announced during the event; keep them out of the
    # listing so participants cannot discover the names in advance. Direct
    # lookups by name (and session start) still work once a name is announced.
    return [s for s in scenarios if "EVAL" not in s.name.upper()]


@router.get("/{name}", response_model=ScenarioResponse)
async def get_scenario(name: str, db: AsyncSession = Depends(get_db)):
    """Get a scenario by name."""
    service = ScenarioService(db)
    scenario = await service.get_by_name(name)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{name}' not found"
        )
    return scenario


@router.get("/{name}/rates", response_model=ScenarioRatesResponse)
async def get_scenario_rates(name: str, db: AsyncSession = Depends(get_db)):
    """Get rates at every timestamp visited by a scenario."""
    scenario_service = ScenarioService(db)
    scenario = await scenario_service.get_by_name(name)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{name}' not found"
        )

    rate_service = RateService(db)
    rates = await rate_service.get_rates_for_timestamps(
        _scenario_timestamps(scenario)
    )
    return ScenarioRatesResponse(
        name=scenario.name,
        start_datetime=scenario.start_datetime,
        end_datetime=scenario.end_datetime,
        date_to_currency_pair_to_rate=rates,
    )


@router.post("/", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    data: ScenarioCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new scenario."""
    service = ScenarioService(db)

    # Check if name already exists
    existing = await service.get_by_name(data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scenario '{data.name}' already exists"
        )

    scenario = await service.create(data)
    return scenario


@router.post("/bulk", response_model=ScenarioBulkResponse)
async def bulk_upload_scenarios(
    data: ScenarioBulkUpload,
    db: AsyncSession = Depends(get_db)
):
    """Bulk upload scenarios.

    Inserts new scenarios or updates existing ones, keyed by name.
    """
    service = ScenarioService(db)

    try:
        inserted, updated = await service.bulk_upsert(data.scenarios)
        return ScenarioBulkResponse(inserted=inserted, updated=updated)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload scenarios: {str(e)}"
        )


@router.put("/{name}", response_model=ScenarioResponse)
async def update_scenario(
    name: str,
    data: ScenarioUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a scenario."""
    service = ScenarioService(db)
    scenario = await service.update(name, data)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{name}' not found"
        )
    return scenario


@router.post("/{scenario_id}/check-rates", response_model=RateCheckResponse)
async def check_scenario_rates(
    scenario_id: int,
    data: RateCheckRequest,
    db: AsyncSession = Depends(get_db),
):
    """Check whether rates exist for all expected timestamps in a scenario.

    Generates every timestamp the scenario would step through (respecting
    weekend skipping for day-sized intervals) and reports which are missing
    for each requested currency.
    """
    scenario_service = ScenarioService(db)
    scenario = await scenario_service.get_by_id(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario {scenario_id} not found",
        )

    # Generate all expected timestamps
    timestamps = _scenario_timestamps(scenario)

    currencies = [c.upper() for c in data.currencies]
    rate_service = RateService(db)
    missing = await rate_service.check_coverage(timestamps, currencies)

    return RateCheckResponse(
        scenario_id=scenario_id,
        currencies=currencies,
        total_expected_timestamps=len(timestamps),
        missing=missing,
        complete=all(len(v) == 0 for v in missing.values()),
    )


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(name: str, db: AsyncSession = Depends(get_db)):
    """Delete a scenario."""
    service = ScenarioService(db)
    deleted = await service.delete(name)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{name}' not found"
        )
