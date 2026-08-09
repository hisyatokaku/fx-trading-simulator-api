"""Pydantic schemas for trade operations."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ExchangeRequest(BaseModel):
    """Single currency exchange request."""

    currency_from: str = Field(..., min_length=3, max_length=10)
    currency_to: str = Field(..., min_length=3, max_length=10)
    amount: float = Field(..., gt=0)


class TradeRequest(BaseModel):
    """Request to execute trades and advance time."""

    session_id: int
    exchange_requests: List[ExchangeRequest] = []


class TradeResult(BaseModel):
    """Result of a single exchange."""

    currency_from: str
    currency_to: str
    amount_from: float
    amount_to: float
    rate: float


class TradeResponse(BaseModel):
    """Response after executing trades."""

    session_id: int
    previous_datetime: datetime
    current_datetime: datetime
    is_complete: bool
    balances: Dict[str, float]
    trades: List[TradeResult] = []
    rates: Dict[str, float] = {}
    jpy_balance: Optional[float] = None
