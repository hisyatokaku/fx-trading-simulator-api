"""Balance model for tracking currency balances over time."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Balance(Base):
    """Currency balance snapshot at a specific timestamp."""

    __tablename__ = "balances"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("trading_sessions.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    currency = Column(String(10), nullable=False)
    amount = Column(Numeric(20, 6), nullable=False)

    # Unique constraint on session_id, timestamp, currency
    __table_args__ = (
        UniqueConstraint("session_id", "timestamp", "currency", name="uq_balance_session_time_currency"),
    )

    # Relationships
    session = relationship("TradingSession", back_populates="balances")

    def __repr__(self):
        return f"<Balance(session={self.session_id}, {self.currency}={self.amount} at {self.timestamp})>"
