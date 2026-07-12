"""Rate model for exchange rates."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Integer, String, DateTime, Numeric, UniqueConstraint, Index

from app.database import Base


class Rate(Base):
    """Exchange rate for a currency at a specific timestamp."""

    __tablename__ = "rates"

    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    rate_to_jpy = Column(Numeric(20, 10), nullable=False)

    # Unique constraint on currency and timestamp
    __table_args__ = (
        UniqueConstraint("currency", "timestamp", name="uq_rate_currency_timestamp"),
        Index("ix_rate_currency_timestamp", "currency", "timestamp"),
    )

    def __repr__(self):
        return f"<Rate({self.currency}={self.rate_to_jpy} JPY at {self.timestamp})>"
