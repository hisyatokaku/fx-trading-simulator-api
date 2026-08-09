"""Pydantic schemas for trading session operations."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class SessionResponse(BaseModel):
    """Schema for trading session response."""

    id: int
    user_id: str
    scenario_id: int
    scenario_name: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    current_datetime: datetime
    time_interval_seconds: int
    is_complete: bool
    jpy_balance: Optional[float] = None
    balances: Dict[str, float] = {}
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """Schema for list of sessions."""

    sessions: List[SessionResponse]
    total: int
