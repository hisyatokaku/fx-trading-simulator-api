"""Pydantic schemas for trader operations."""

from typing import List

from pydantic import BaseModel, Field


class TraderEntry(BaseModel):
    """Single trader entry."""

    user_id: str = Field(..., min_length=1, max_length=50)
    type: str = Field(default="test", pattern="^(prod|test)$")


class TraderBulkUpload(BaseModel):
    """Bulk trader upload request."""

    traders: List[TraderEntry]


class TraderBulkResponse(BaseModel):
    """Response after bulk trader upload."""

    inserted: int
    updated: int
