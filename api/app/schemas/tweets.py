"""Pydantic schemas for tweet responses."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Tweet(BaseModel):
    """Tweet model for API responses."""

    id: int = Field(..., description="Tweet database ID")
    text: str = Field(..., description="Tweet text content")
    like_count: int = Field(default=0, description="Number of likes")
    retweet_count: int = Field(default=0, description="Number of retweets")
    created_at: Optional[datetime] = Field(default=None, description="When the tweet was created on X")
    scraped_at: datetime = Field(..., description="When the tweet was scraped and stored")
    username: Optional[str] = Field(default=None, description="X username associated with the tweet")

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models


class TweetList(BaseModel):
    """Response containing a list of tweets."""

    tweets: List[Tweet] = Field(default_factory=list, description="List of tweets")

