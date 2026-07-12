"""Trader model."""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.database import Base


class Trader(Base):
    """Trader/user entity."""

    __tablename__ = "traders"

    user_id = Column(String(50), primary_key=True)
    type = Column(String(20), nullable=False, default="test")  # 'prod' or 'test'

    # Relationships
    sessions = relationship("TradingSession", back_populates="trader")

    def __repr__(self):
        return f"<Trader(user_id='{self.user_id}', type='{self.type}')>"
