"""Pydantic schemas for rate operations."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from pydantic import BaseModel, Field


class RateEntry(BaseModel):
    """Single rate entry."""

    currency: str = Field(..., min_length=3, max_length=10)
    timestamp: datetime
    rate_to_jpy: Decimal = Field(..., gt=0)


class RateBulkUpload(BaseModel):
    """Bulk rate upload request."""

    rates: List[RateEntry]


class RateResponse(BaseModel):
    """Response containing rates for a timestamp."""

    timestamp: datetime
    rates: Dict[str, Decimal]


class RateBulkResponse(BaseModel):
    """Response after bulk rate upload."""

    inserted: int
    updated: int
    errors: List[str] = []
