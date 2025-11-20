"""Trade recommendation models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .analysis import FundamentalAnalysis, TechnicalAnalysis, SentimentAnalysis, RiskAnalysis


class TradeDirection(str, Enum):
    """Trade direction."""

    LONG = "long"
    SHORT = "short"


class TradeTimeframe(str, Enum):
    """Trade timeframe."""

    SCALP = "scalp"  # Minutes to hours
    DAY = "day"      # Same day
    SWING = "swing"  # Days to weeks
    POSITION = "position"  # Weeks to months


class TradeEntry(BaseModel):
    """Trade entry point details."""

    model_config = ConfigDict(
        json_encoders={
            Decimal: str
        }
    )

    price: Decimal = Field(..., description="Entry price")
    quantity: int = Field(..., description="Number of shares/units")
    order_type: str = Field("market", description="Order type (market/limit/stop)")
    confidence: float = Field(..., description="Confidence level (0-100)")


class TradeExit(BaseModel):
    """Trade exit point details."""

    model_config = ConfigDict(
        json_encoders={
            Decimal: str
        }
    )

    stop_loss: Decimal = Field(..., description="Stop loss price")
    take_profit: List[Decimal] = Field(..., description="Take profit levels")
    stop_loss_percent: Decimal = Field(..., description="Stop loss percentage from entry")
    take_profit_percents: List[Decimal] = Field(..., description="Take profit percentages")


class TradeRisk(BaseModel):
    """Trade risk assessment."""

    model_config = ConfigDict(
        json_encoders={
            Decimal: str
        }
    )

    risk_reward_ratio: Decimal = Field(..., description="Risk to reward ratio")
    position_size_percent: Decimal = Field(..., description="Position size as % of portfolio")
    max_loss_amount: Decimal = Field(..., description="Maximum potential loss")
    max_gain_amount: Decimal = Field(..., description="Maximum potential gain")
    probability_of_success: float = Field(..., description="Estimated probability of success")
    risk_level: str = Field(..., description="Risk level (low/medium/high)")


class TradeRecommendation(BaseModel):
    """Complete trade recommendation."""

    symbol: str = Field(..., description="Trading symbol")
    direction: TradeDirection = Field(..., description="Trade direction")
    timeframe: TradeTimeframe = Field(..., description="Expected trade duration")
    entry: TradeEntry = Field(..., description="Entry details")
    exit: TradeExit = Field(..., description="Exit strategy")
    risk: TradeRisk = Field(..., description="Risk assessment")

    # Analysis components
    fundamental_analysis: Optional[FundamentalAnalysis] = Field(None, description="Fundamental analysis")
    technical_analysis: Optional[TechnicalAnalysis] = Field(None, description="Technical analysis")
    sentiment_analysis: Optional[SentimentAnalysis] = Field(None, description="Sentiment analysis")
    risk_analysis: Optional[RiskAnalysis] = Field(None, description="Risk analysis")

    # Summary
    overall_score: float = Field(..., description="Overall recommendation score (0-100)")
    confidence_level: float = Field(..., description="Overall confidence (0-100)")
    reasoning: str = Field(..., description="Detailed reasoning for the recommendation")
    key_factors: List[str] = Field(..., description="Key factors supporting the trade")
    potential_catalysts: List[str] = Field(default_factory=list, description="Potential trade catalysts")
    risks: List[str] = Field(..., description="Key risks to monitor")

    created_at: datetime = Field(default_factory=datetime.now, description="Recommendation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Recommendation expiry")

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    )