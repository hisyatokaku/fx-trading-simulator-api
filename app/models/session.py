"""Trading session model."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class TradingSession(Base):
    """Trading session for a user in a scenario."""

    __tablename__ = "trading_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("traders.user_id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    current_datetime = Column(DateTime, nullable=False)
    time_interval_seconds = Column(Integer, nullable=False)
    is_complete = Column(Boolean, default=False)
    jpy_balance = Column(Numeric(20, 6))
    created_at = Column(DateTime, default=func.now())

    # Relationships
    trader = relationship("Trader", back_populates="sessions")
    scenario = relationship("Scenario", back_populates="sessions")
    balances = relationship("Balance", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TradingSession(id={self.id}, user='{self.user_id}', scenario_id={self.scenario_id})>"
