"""API request/response models."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from ..models import TradingInstrument
from ..models.trade import TradeRecommendation


class InstrumentRequest(BaseModel):
    """Request model for trading instruments."""

    symbol: str = Field(..., description="Trading symbol")
    name: str = Field(..., description="Instrument name")
    instrument_type: str = Field(..., description="Type of instrument")
    exchange: Optional[str] = Field(None, description="Exchange")
    currency: str = Field("USD", description="Currency")
    sector: Optional[str] = Field(None, description="Sector")
    is_favorite: bool = Field(True, description="Is favorite instrument")


class AnalysisRequest(BaseModel):
    """Request model for trading analysis."""

    favorite_instruments: List[InstrumentRequest] = Field(
        ..., description="List of favorite trading instruments to analyze"
    )
    portfolio_data: Optional[Dict] = Field(
        None, description="Optional portfolio data for risk management"
    )
    analysis_preferences: Optional[Dict] = Field(
        None, description="Optional analysis preferences"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "favorite_instruments": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "instrument_type": "stock",
                        "exchange": "NASDAQ",
                        "currency": "USD",
                        "sector": "Technology",
                        "is_favorite": True
                    }
                ],
                "portfolio_data": {
                    "total_value": 100000,
                    "cash_available": 20000,
                    "risk_tolerance": "moderate"
                }
            }
        }


class AnalysisResponse(BaseModel):
    """Response model for trading analysis."""

    recommendations: List[TradeRecommendation] = Field(
        ..., description="List of trade recommendations"
    )
    total_analyzed: int = Field(..., description="Total instruments analyzed")
    total_recommended: int = Field(..., description="Total recommendations generated")
    analysis_timestamp: str = Field(..., description="Analysis completion timestamp")
    summary: Optional[str] = Field(None, description="Analysis summary")

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "recommendations": [],
                "total_analyzed": 5,
                "total_recommended": 3,
                "analysis_timestamp": "2024-01-01T12:00:00Z",
                "summary": "Generated 3 trade recommendations from 5 analyzed instruments"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Error details")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())