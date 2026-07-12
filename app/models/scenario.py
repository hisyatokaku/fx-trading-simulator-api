"""Scenario model - replaces GameConfig enum from Java."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Numeric, func
from sqlalchemy.orm import relationship

from app.database import Base


class Scenario(Base):
    """Trading scenario configuration."""

    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    time_interval_seconds = Column(Integer, nullable=False, default=86400)  # 86400 = 1 day
    game_type = Column(String(20), default="ANY")  # 'PROD' or 'ANY'
    initial_balance = Column(Numeric(20, 6), default=1000000)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    sessions = relationship("TradingSession", back_populates="scenario")

    def __repr__(self):
        return f"<Scenario(name='{self.name}', interval={self.time_interval_seconds}s)>"
