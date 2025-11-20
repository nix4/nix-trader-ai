"""Analysis models for trading decisions."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AnalysisSignal(str, Enum):
    """Analysis signal types."""

    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class FundamentalAnalysis(BaseModel):
    """Fundamental analysis results."""

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    )

    symbol: str = Field(..., description="Trading symbol")
    pe_ratio: Optional[Decimal] = Field(None, description="Price-to-earnings ratio")
    pb_ratio: Optional[Decimal] = Field(None, description="Price-to-book ratio")
    debt_to_equity: Optional[Decimal] = Field(None, description="Debt-to-equity ratio")
    roe: Optional[Decimal] = Field(None, description="Return on equity")
    revenue_growth: Optional[Decimal] = Field(None, description="Revenue growth percentage")
    earnings_growth: Optional[Decimal] = Field(None, description="Earnings growth percentage")
    dividend_yield: Optional[Decimal] = Field(None, description="Dividend yield")
    free_cash_flow: Optional[Decimal] = Field(None, description="Free cash flow")
    signal: AnalysisSignal = Field(..., description="Fundamental analysis signal")
    score: float = Field(..., description="Fundamental score (0-100)")
    reasoning: str = Field(..., description="Analysis reasoning")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class TechnicalIndicator(BaseModel):
    """Technical indicator value."""

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            Decimal: str
        }
    )

    name: str = Field(..., description="Indicator name")
    value: Decimal = Field(..., description="Indicator value")
    signal: Optional[AnalysisSignal] = Field(None, description="Indicator signal")


class SupportResistanceLevel(BaseModel):
    """Support or resistance level with metadata."""

    model_config = ConfigDict(
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    )

    price: Decimal = Field(..., description="Price level")
    level_type: str = Field(..., description="Type: 'support' or 'resistance'")
    strength: float = Field(..., description="Level strength (0.0 to 1.0)")
    touches: int = Field(..., description="Number of times price touched this level")
    last_touch_date: Optional[datetime] = Field(None, description="Last time level was touched")


class ChartPattern(BaseModel):
    """Identified chart pattern."""

    pattern_type: str = Field(..., description="Pattern type (e.g., 'uptrend', 'triangle')")
    strength: float = Field(..., description="Pattern strength (0.0 to 1.0)")
    description: str = Field(..., description="Pattern description")
    timeframe: str = Field(..., description="Pattern timeframe")


class TechnicalAnalysis(BaseModel):
    """Technical analysis results."""

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    )

    symbol: str = Field(..., description="Trading symbol")
    indicators: List[TechnicalIndicator] = Field(..., description="Technical indicators")
    support_levels: List[SupportResistanceLevel] = Field(default_factory=list, description="Identified support levels")
    resistance_levels: List[SupportResistanceLevel] = Field(default_factory=list, description="Identified resistance levels")
    fibonacci_levels: Dict[str, Decimal] = Field(default_factory=dict, description="Fibonacci retracement levels")
    chart_patterns: List[ChartPattern] = Field(default_factory=list, description="Identified chart patterns")
    trend_direction: str = Field(..., description="Overall trend direction")
    trend_strength: float = Field(0.0, description="Trend strength (0.0 to 1.0)")
    key_levels: Dict[str, Decimal] = Field(default_factory=dict, description="Key price levels to watch")
    signal: AnalysisSignal = Field(..., description="Technical analysis signal")
    score: float = Field(..., description="Technical score (0-100)")
    reasoning: str = Field(..., description="Analysis reasoning")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class SentimentAnalysis(BaseModel):
    """Sentiment analysis results."""

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )

    symbol: str = Field(..., description="Trading symbol")
    overall_sentiment: float = Field(..., description="Overall sentiment score (-1 to 1)")
    news_sentiment: float = Field(..., description="News sentiment score (-1 to 1)")
    social_sentiment: Optional[float] = Field(None, description="Social media sentiment (-1 to 1)")
    analyst_sentiment: Optional[float] = Field(None, description="Analyst sentiment (-1 to 1)")
    sentiment_sources: int = Field(..., description="Number of sentiment sources analyzed")
    signal: AnalysisSignal = Field(..., description="Sentiment analysis signal")
    score: float = Field(..., description="Sentiment score (0-100)")
    reasoning: str = Field(..., description="Analysis reasoning")
    key_themes: List[str] = Field(default_factory=list, description="Key sentiment themes")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class RiskFactor(BaseModel):
    """Individual risk factor."""

    name: str = Field(..., description="Risk factor name")
    severity: str = Field(..., description="Risk severity (low/medium/high)")
    probability: float = Field(..., description="Risk probability (0-1)")
    impact: str = Field(..., description="Risk impact description")


class RiskAnalysis(BaseModel):
    """Risk analysis results."""

    model_config = ConfigDict(
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    )

    symbol: str = Field(..., description="Trading symbol")
    overall_risk_score: float = Field(..., description="Overall risk score (0-100)")
    volatility_risk: float = Field(..., description="Volatility risk score (0-100)")
    liquidity_risk: float = Field(..., description="Liquidity risk score (0-100)")
    market_risk: float = Field(..., description="Market risk score (0-100)")
    fundamental_risk: float = Field(..., description="Fundamental risk score (0-100)")
    risk_factors: List[RiskFactor] = Field(default_factory=list, description="Identified risk factors")
    max_position_size: Decimal = Field(..., description="Maximum recommended position size")
    recommended_stop_loss: Decimal = Field(..., description="Recommended stop loss percentage")
    reasoning: str = Field(..., description="Risk analysis reasoning")
    analyzed_at: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")