"""Session service for managing trading sessions."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.session import TradingSession
from app.models.balance import Balance
from app.models.scenario import Scenario
from app.schemas.trade import ExchangeRequest, TradeResult
from app.services.rate_service import RateService
from app.utils.date_utils import add_interval


# Supported currencies
CURRENCIES = [
    "JPY", "USD", "EUR", "GBP", "AUD", "NZD", "CAD", "CHF",
    "TRY", "ZAR", "MXN", "NOK", "SEK", "HKD",
]

# Users allowed to start sessions (no DB call; kept in code by design).
# Sources: infra-setup/users/participants.txt (60) + testers.txt (8) + ops IDs (5).
# NOTE: adding an ID requires BOTH adding it here (and redeploying) AND registering
# it in the traders table (trading_sessions.user_id has a FK to traders).
ALLOWED_USER_IDS = frozenset([
    # participants (2026-09-02)
    "5rkk8", "3qs9z", "f2h85", "pctmu", "37x74", "vry9t",
    "4wq3c", "wp5wn", "5zdcz", "qzreg", "up35z", "4346t",
    "byugp", "8x96n", "zth7w", "wbjfz", "egke5", "hhwqb",
    "hze6m", "xjb8q", "ex8zc", "y8u48", "j6wk9", "skj7d",
    "dbhdr", "kjnyz", "hzvbg", "k5tpr", "x5zjw", "qm2kk",
    "2vtsr", "2rx57", "9pb9m", "6ukdt", "b28vk", "y3xy7",
    "2w3cb", "24reh", "z73g6", "4jc96", "g34a9", "kmtg9",
    "qxvm2", "7zd3j", "eju96", "dwk9b", "ph6ua", "tr7g3",
    "g8r2f", "6tccp", "qkgyq", "qu7ka", "hrre5", "nt3rk",
    "bd7u3", "h8qfh", "j7p6d", "tfekb", "xf9am", "na59y",
    # testers
    "tester-1", "tester-2", "tester-3", "tester-4", "tester-5", "tester-6",
    "tester-7", "tester-8",
    # ops / e2e
    "testuser", "demouser", "yukiyk", "produser", "latency-check",
])


class AlreadySubmittedError(Exception):
    """A completed evaluation session already exists for this user/scenario."""


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
        # Reject users that are not on the allowlist
        self._check_user_allowed(user_id)

        # Evaluation scenarios accept one submission per user: once a
        # completed session exists, further starts are rejected (409).
        # Incomplete sessions (crashed kernel, dropped connection) may be
        # restarted, so genuine accidents need no operator intervention.
        if "EVAL" in scenario.name.upper():
            result = await self.db.execute(
                select(TradingSession.id).where(
                    TradingSession.user_id == user_id,
                    TradingSession.scenario_id == scenario.id,
                    TradingSession.is_complete.is_(True),
                ).limit(1)
            )
            if result.scalar_one_or_none() is not None:
                raise AlreadySubmittedError(
                    f"Scenario '{scenario.name}' has already been submitted by "
                    f"'{user_id}' (evaluation runs are accepted once)"
                )

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

    @staticmethod
    def _check_user_allowed(user_id: str) -> None:
        """Reject user_ids that are not on the hardcoded allowlist (no DB call)."""
        if user_id not in ALLOWED_USER_IDS:
            raise PermissionError(
                f"user_id '{user_id}' is not registered. Use the ID distributed by the staff."
            )

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

        # Calculate JPY balance (total value in JPY) at the tick we just advanced to,
        # so jpy_balance always reports the total at current_datetime -- the final score
        # is therefore valued at the scenario's end tick, not the one before it.
        # If that tick has no rates, fall back to the traded tick so a gap in the rate
        # data cannot fail an otherwise valid trade.
        try:
            valuation_matrix = await self.rate_service.get_rate_matrix(new_datetime)
        except RuntimeError:
            valuation_matrix = rate_matrix

        jpy_balance = await self._calculate_jpy_balance(balances, valuation_matrix)
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
