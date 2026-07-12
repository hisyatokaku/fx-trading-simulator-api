"""Trade API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.session import SessionResponse, SessionListResponse
from app.schemas.trade import TradeRequest, TradeResponse
from app.services.scenario_service import ScenarioService
from app.services.session_service import SessionService

router = APIRouter()


def _build_session_response(session, balances: dict = None) -> SessionResponse:
    """Build SessionResponse from a TradingSession."""
    if balances is None:
        # Build balances from loaded relationship
        balances = {}
        if session.balances:
            current_balances = [
                b for b in session.balances
                if b.timestamp == session.current_datetime
            ]
            balances = {b.currency: b.amount for b in current_balances}

    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        scenario_id=session.scenario_id,
        scenario_name=session.scenario.name if session.scenario else None,
        start_datetime=session.start_datetime,
        end_datetime=session.end_datetime,
        current_datetime=session.current_datetime,
        time_interval_seconds=session.time_interval_seconds,
        is_complete=session.is_complete,
        jpy_balance=float(session.jpy_balance) if session.jpy_balance is not None else None,
        balances={k: float(v) for k, v in balances.items()},
        created_at=session.created_at,
    )


@router.post("/start/{scenario}/{user_id}", response_model=SessionResponse)
async def start_session(
    scenario: str,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Start a new trading session.

    Args:
        scenario: Name of the scenario to use
        user_id: User identifier
    """
    # Get scenario
    scenario_service = ScenarioService(db)
    scenario_obj = await scenario_service.get_by_name(scenario)

    if not scenario_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario}' not found"
        )

    # Create session
    session_service = SessionService(db)
    session = await session_service.start_session(user_id, scenario_obj)

    # Get initial balances
    balances = await session_service.get_current_balances(session)

    return _build_session_response(session, balances)


@router.post("/next", response_model=TradeResponse)
async def execute_next(
    request: TradeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute trades and advance to next time period.

    Args:
        request: Trade request containing session_id and exchange requests
    """
    session_service = SessionService(db)
    session = await session_service.get_session(request.session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {request.session_id} not found"
        )

    if session.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already complete"
        )

    previous_datetime = session.current_datetime

    try:
        session, trade_results, rates = await session_service.execute_trades_and_advance(
            session, request.exchange_requests
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Get updated balances
    balances = await session_service.get_current_balances(session)

    return TradeResponse(
        session_id=session.id,
        previous_datetime=previous_datetime,
        current_datetime=session.current_datetime,
        is_complete=session.is_complete,
        balances={k: float(v) for k, v in balances.items()},
        trades=trade_results,
        rates={k: float(v) for k, v in rates.items()},
        jpy_balance=float(session.jpy_balance) if session.jpy_balance is not None else None,
    )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get session details by ID."""
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

    balances = await session_service.get_current_balances(session)
    return _build_session_response(session, balances)


@router.get("/sessions/{user_id}", response_model=SessionListResponse)
async def get_user_sessions(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all sessions for a user."""
    session_service = SessionService(db)
    sessions = await session_service.get_user_sessions(user_id)

    session_responses = []
    for session in sessions:
        balances = await session_service.get_current_balances(session)
        session_responses.append(_build_session_response(session, balances))

    return SessionListResponse(
        sessions=session_responses,
        total=len(session_responses),
    )
