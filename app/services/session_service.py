"""Session service for managing trading sessions."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.session import TradingSession
from app.models.balance import Balance
from app.models.trader import Trader
from app.models.scenario import Scenario
from app.schemas.trade import ExchangeRequest, TradeResult
from app.services.rate_service import RateService
from app.utils.date_utils import add_interval


# Supported currencies
CURRENCIES = [
    "JPY", "USD", "EUR", "GBP", "AUD", "NZD", "CAD", "CHF",
    "TRY", "ZAR", "MXN", "NOK", "SEK", "HKD",
]


class SessionService:
    """Service for trading session operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rate_service = RateService(db)

    async def start_session(
        self,
        user_id: str,
        scenario: Scenario
    ) -> TradingSession:
        """Start a new trading session for a user in a scenario."""
        # Ensure trader exists
        trader = await self._ensure_trader(user_id, scenario.game_type)

        # Create session
        session = TradingSession(
            user_id=user_id,
            scenario_id=scenario.id,
            start_datetime=scenario.start_datetime,
            end_datetime=scenario.end_datetime,
            current_datetime=scenario.start_datetime,
            time_interval_seconds=scenario.time_interval_seconds,
            is_complete=False,
        )
        self.db.add(session)
        await self.db.flush()

        # Initialize balances with initial JPY balance
        initial_balance = Balance(
            session_id=session.id,
            timestamp=scenario.start_datetime,
            currency="JPY",
            amount=scenario.initial_balance,
        )
        self.db.add(initial_balance)

        # Initialize other currencies with 0
        for currency in CURRENCIES:
            if currency != "JPY":
                balance = Balance(
                    session_id=session.id,
                    timestamp=scenario.start_datetime,
                    currency=currency,
                    amount=Decimal("0"),
                )
                self.db.add(balance)

        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def _ensure_trader(self, user_id: str, game_type: str) -> Trader:
        """Ensure trader exists, create if not."""
        result = await self.db.execute(
            select(Trader).where(Trader.user_id == user_id)
        )
        trader = result.scalar_one_or_none()

        if not trader:
            trader_type = "prod" if game_type == "PROD" else "test"
            trader = Trader(user_id=user_id, type=trader_type)
            self.db.add(trader)
            await self.db.flush()

        return trader

    async def get_session(self, session_id: int) -> Optional[TradingSession]:
        """Get a session by ID with its scenario loaded."""
        result = await self.db.execute(
            select(TradingSession)
            .options(joinedload(TradingSession.scenario))
            .where(TradingSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_user_sessions(self, user_id: str) -> List[TradingSession]:
        """Get all sessions for a user."""
        result = await self.db.execute(
            select(TradingSession)
            .options(selectinload(TradingSession.scenario))
            .where(TradingSession.user_id == user_id)
            .order_by(TradingSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_current_balances(self, session: TradingSession) -> Dict[str, Decimal]:
        """Get current balances for a session."""
        result = await self.db.execute(
            select(Balance)
            .where(and_(
                Balance.session_id == session.id,
                Balance.timestamp == session.current_datetime
            ))
        )
        balances = result.scalars().all()
        return {b.currency: b.amount for b in balances}

    async def get_balance_history(self, session_id: int) -> Dict[str, Dict[str, Decimal]]:
        """Get every balance snapshot for a session, grouped by timestamp."""
        result = await self.db.execute(
            select(Balance)
            .where(Balance.session_id == session_id)
            .order_by(Balance.timestamp, Balance.currency)
        )

        history: Dict[str, Dict[str, Decimal]] = {}
        for balance in result.scalars().all():
            timestamp = balance.timestamp.isoformat()
            history.setdefault(timestamp, {})[balance.currency] = balance.amount
        return history

    async def execute_trades_and_advance(
        self,
        session: TradingSession,
        exchange_requests: List[ExchangeRequest]
    ) -> Tuple[TradingSession, List[TradeResult], Dict[str, Decimal], Dict[str, Decimal]]:
        """Execute trades and advance time.

        Returns tuple of (updated_session, trade_results, current_rates, balances).
        """
        if session.is_complete:
            raise ValueError("Session is already complete")

        # Get current balances
        balances = await self.get_current_balances(session)

        # Get rate matrix for current time
        rate_matrix = await self.rate_service.get_rate_matrix(session.current_datetime)
        current_rates = rate_matrix.get_all_rates()

        # Execute each trade
        trade_results = []
        for request in exchange_requests:
            result = await self._execute_single_trade(
                balances,
                request,
                rate_matrix,
            )
            if result:
                trade_results.append(result)

        # Advance time
        previous_datetime = session.current_datetime
        new_datetime = add_interval(session.current_datetime, session.time_interval_seconds)

        # Check if session is complete
        is_complete = new_datetime >= session.end_datetime
        if is_complete:
            new_datetime = session.end_datetime

        session.current_datetime = new_datetime
        session.is_complete = is_complete

        # Calculate JPY balance (total value in JPY)
        jpy_balance = await self._calculate_jpy_balance(balances, rate_matrix)
        session.jpy_balance = jpy_balance

        # Save new balances at new timestamp
        for currency, amount in balances.items():
            balance = Balance(
                session_id=session.id,
                timestamp=new_datetime,
                currency=currency,
                amount=amount,
            )
            self.db.add(balance)

        await self.db.flush()

        return session, trade_results, current_rates, balances

    async def _execute_single_trade(
        self,
        balances: Dict[str, Decimal],
        request: ExchangeRequest,
        rate_matrix,
    ) -> Optional[TradeResult]:
        """Execute a single trade, updating balances in place."""
        currency_from = request.currency_from.upper()
        currency_to = request.currency_to.upper()

        current_balance = balances.get(currency_from, Decimal("0"))
        if current_balance < request.amount:
            return None

        converted_amount, rate = rate_matrix.convert(
            Decimal(str(request.amount)),
            currency_from,
            currency_to,
        )

        if converted_amount is None:
            return None

        balances[currency_from] = current_balance - Decimal(str(request.amount))
        balances[currency_to] = balances.get(currency_to, Decimal("0")) + converted_amount

        return TradeResult(
            currency_from=currency_from,
            currency_to=currency_to,
            amount_from=float(request.amount),
            amount_to=float(converted_amount),
            rate=float(rate),
        )

    async def _calculate_jpy_balance(
        self,
        balances: Dict[str, Decimal],
        rate_matrix
    ) -> Decimal:
        """Calculate total portfolio value in JPY."""
        total_jpy = Decimal("0")

        for currency, amount in balances.items():
            if currency == "JPY":
                total_jpy += amount
            else:
                rate = rate_matrix.get_rate(currency, "JPY")
                if rate:
                    total_jpy += amount * rate

        return total_jpy.quantize(Decimal("0.000001"))
