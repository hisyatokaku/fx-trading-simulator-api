"""Pydantic schemas for scenario operations."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ScenarioBase(BaseModel):
    """Base schema for scenario data."""

    name: str = Field(..., min_length=1, max_length=100)
    start_datetime: datetime
    end_datetime: datetime
    time_interval_seconds: int = Field(default=86400, ge=1)
    game_type: str = Field(default="ANY", pattern="^(PROD|ANY)$")
    initial_balance: float = Field(default=1000000.0, ge=0)

    @field_validator("end_datetime")
    @classmethod
    def end_must_be_after_start(cls, v, info):
        if "start_datetime" in info.data and v <= info.data["start_datetime"]:
            raise ValueError("end_datetime must be after start_datetime")
        return v


class ScenarioCreate(ScenarioBase):
    """Schema for creating a scenario."""

    pass


class ScenarioUpdate(BaseModel):
    """Schema for updating a scenario."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    time_interval_seconds: Optional[int] = Field(None, ge=1)
    game_type: Optional[str] = Field(None, pattern="^(PROD|ANY)$")
    initial_balance: Optional[float] = Field(None, ge=0)


class RateCheckRequest(BaseModel):
    """Request body for checking rate coverage of a scenario."""

    currencies: List[str] = Field(..., min_length=1)


class RateCheckResponse(BaseModel):
    """Response showing which timestamps are missing rates for each currency."""

    scenario_id: int
    currencies: List[str]
    total_expected_timestamps: int
    missing: Dict[str, List[datetime]]
    complete: bool


class ScenarioResponse(BaseModel):
    """Schema for scenario response."""

    id: int
    name: str
    start_datetime: datetime
    end_datetime: datetime
    time_interval_seconds: int
    game_type: str
    initial_balance: float
    created_at: datetime

    model_config = {"from_attributes": True}
