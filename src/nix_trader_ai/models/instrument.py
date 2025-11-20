"""Trading instrument models."""

from enum import Enum
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InstrumentType(str, Enum):
    """Types of trading instruments."""

    STOCK = "stock"
    ETF = "etf"
    FOREX = "forex"
    CRYPTOCURRENCY = "cryptocurrency"
    COMMODITY = "commodity"
    BOND = "bond"
    OPTION = "option"
    FUTURE = "future"


class TradingInstrument(BaseModel):
    """Represents a trading instrument."""

    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            Decimal: str
        }
    )

    symbol: str = Field(..., description="Trading symbol (e.g., AAPL, EUR/USD)")
    name: str = Field(..., description="Full name of the instrument")
    instrument_type: InstrumentType = Field(..., description="Type of instrument")
    exchange: Optional[str] = Field(None, description="Exchange where traded")
    currency: str = Field("USD", description="Base currency")
    sector: Optional[str] = Field(None, description="Sector for stocks/ETFs")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")
    is_favorite: bool = Field(False, description="Whether this is a favorite instrument")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")