"""Market data models."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PriceData(BaseModel):
    """Price data for an instrument."""

    model_config = ConfigDict(
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    )

    symbol: str = Field(..., description="Trading symbol")
    timestamp: datetime = Field(..., description="Price timestamp")
    open_price: Decimal = Field(..., description="Opening price")
    high_price: Decimal = Field(..., description="High price")
    low_price: Decimal = Field(..., description="Low price")
    close_price: Decimal = Field(..., description="Closing price")
    volume: Optional[int] = Field(None, description="Trading volume")
    adjusted_close: Optional[Decimal] = Field(None, description="Adjusted closing price")


class NewsItem(BaseModel):
    """News item for sentiment analysis."""

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

    title: str = Field(..., description="News headline")
    content: str = Field(..., description="Full article content")
    source: str = Field(..., description="News source")
    published_at: datetime = Field(..., description="Publication timestamp")
    url: Optional[str] = Field(None, description="Article URL")
    symbols: List[str] = Field(default_factory=list, description="Related symbols")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score (-1 to 1)")


class MarketData(BaseModel):
    """Comprehensive market data for an instrument."""

    model_config = ConfigDict(
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    )

    symbol: str = Field(..., description="Trading symbol")
    current_price: Decimal = Field(..., description="Current market price")
    price_history: List[PriceData] = Field(default_factory=list, description="Historical price data")
    volume_24h: Optional[int] = Field(None, description="24-hour trading volume")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")
    pe_ratio: Optional[Decimal] = Field(None, description="Price-to-earnings ratio")
    dividend_yield: Optional[Decimal] = Field(None, description="Dividend yield percentage")
    beta: Optional[Decimal] = Field(None, description="Beta coefficient")
    fifty_two_week_high: Optional[Decimal] = Field(None, description="52-week high")
    fifty_two_week_low: Optional[Decimal] = Field(None, description="52-week low")
    average_volume: Optional[int] = Field(None, description="Average trading volume")
    news_items: List[NewsItem] = Field(default_factory=list, description="Related news")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")