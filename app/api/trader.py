"""Trader API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.trader import TraderBulkUpload, TraderBulkResponse
from app.services.trader_service import TraderService

router = APIRouter()


@router.post("/bulk", response_model=TraderBulkResponse)
async def bulk_upload_traders(
    data: TraderBulkUpload,
    db: AsyncSession = Depends(get_db)
):
    """Bulk upload traders.

    Inserts new traders or updates existing ones' type, keyed by user_id.
    """
    service = TraderService(db)

    try:
        inserted, updated = await service.bulk_upsert(data.traders)
        return TraderBulkResponse(inserted=inserted, updated=updated)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload traders: {str(e)}"
        )
