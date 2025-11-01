"""SQLAlchemy model for tweets."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, Text

from ..core.database import Base


class Tweet(Base):
    """Tweet model for storing scraped tweets."""

    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    retweet_count = Column(Integer, default=0)
    created_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
