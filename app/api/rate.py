"""Rate API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.rate import RateResponse, RateBulkUpload, RateBulkResponse
from app.services.rate_service import RateService
from app.utils.date_utils import parse_datetime

router = APIRouter()


@router.get("/{timestamp}", response_model=RateResponse)
async def get_rates(
    timestamp: str,
    db: AsyncSession = Depends(get_db)
):
    """Get exchange rates for a timestamp. Returns 404 if no rates exist at that exact timestamp."""
    try:
        dt = parse_datetime(timestamp)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timestamp format: {timestamp}"
        )

    service = RateService(db)

    try:
        rates = await service.get_rates_at_timestamp(dt)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    return RateResponse(timestamp=dt, rates=rates)


@router.post("/bulk", response_model=RateBulkResponse)
async def bulk_upload_rates(
    data: RateBulkUpload,
    db: AsyncSession = Depends(get_db)
):
    """Bulk upload exchange rates.

    Inserts new rates or updates existing ones based on currency+timestamp.
    """
    service = RateService(db)

    try:
        inserted, updated = await service.bulk_upsert(data.rates)
        return RateBulkResponse(inserted=inserted, updated=updated)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload rates: {str(e)}"
        )
