"""Market data aggregation service."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import logfire
from loguru import logger

from ..models.instrument import TradingInstrument
from ..models.market_data import MarketData, NewsItem, PriceData
from ..core.config import settings
from .alpha_vantage_service import AlphaVantageService
from .yfinance_service import YFinanceService
from .interactive_brokers_service import InteractiveBrokersService


class MarketDataService:
    """Service for aggregating market data from multiple sources."""

    def __init__(self):
        """Initialize the market data service."""
        self.alpha_vantage = AlphaVantageService()
        self.yfinance = YFinanceService()

        # Initialize IB service if enabled
        self.ib_service = None
        if settings.enable_ib:
            self.ib_service = InteractiveBrokersService(
                host=settings.ib_host,
                port=settings.ib_port,
                client_id=settings.ib_client_id
            )

        self.logger = logger.bind(service="market_data")

    @logfire.instrument("get_market_data", extract_args=True)
    async def get_market_data(self, instrument: TradingInstrument) -> MarketData:
        """Get comprehensive market data for an instrument."""
        try:
            self.logger.info(f"Fetching market data for {instrument.symbol}")

            with logfire.span("fetch_market_data_components", symbol=instrument.symbol):
                # Get current quote with fallback
                with logfire.span("get_quote", symbol=instrument.symbol):
                    quote_data = await self._get_quote_with_fallback(instrument.symbol)

                # Get price history with fallback
                with logfire.span("get_price_history", symbol=instrument.symbol):
                    price_history = await self._get_price_history_with_fallback(instrument.symbol, 100)

                # Get company overview for fundamentals with fallback
                with logfire.span("get_company_overview", symbol=instrument.symbol):
                    overview_data = await self._get_company_overview_with_fallback(instrument.symbol)

                # Get news data with fallback
                with logfire.span("get_news", symbol=instrument.symbol):
                    news_items = await self._get_news_with_fallback([instrument.symbol], 10)

            # Validate essential data quality
            validation_issues = self._validate_market_data(quote_data, price_history, instrument.symbol)
            if validation_issues:
                self.logger.error(f"Market data validation failed for {instrument.symbol}: {validation_issues}")
                # Don't return None, but log the issues for awareness
                logfire.error(
                    "Market data validation issues",
                    symbol=instrument.symbol,
                    issues=validation_issues,
                    current_price=float(quote_data.get("price", Decimal("0"))),
                    price_history_count=len(price_history)
                )

            # Build market data object
            market_data = MarketData(
                symbol=instrument.symbol,
                current_price=quote_data.get("price", Decimal("0")),
                price_history=price_history,
                volume_24h=quote_data.get("volume"),
                market_cap=self._parse_market_cap(overview_data.get("market_cap")),
                pe_ratio=self._parse_decimal(overview_data.get("pe_ratio")),
                dividend_yield=self._parse_decimal(overview_data.get("dividend_yield")),
                beta=self._parse_decimal(overview_data.get("beta")),
                fifty_two_week_high=self._parse_decimal(overview_data.get("52_week_high")),
                fifty_two_week_low=self._parse_decimal(overview_data.get("52_week_low")),
                news_items=news_items,
                last_updated=datetime.now()
            )

            self.logger.info(f"Successfully fetched market data for {instrument.symbol}")

            logfire.info(
                "Market data fetched successfully",
                symbol=instrument.symbol,
                current_price=float(market_data.current_price),
                price_history_count=len(market_data.price_history),
                news_count=len(market_data.news_items),
                has_fundamentals=bool(overview_data.get("name") or overview_data.get("sector")),
                validation_issues=validation_issues or []
            )

            return market_data

        except Exception as e:
            self.logger.error(f"Error fetching market data for {instrument.symbol}: {str(e)}")
            logfire.error("Market data fetch failed", symbol=instrument.symbol, error=str(e))
            # Return empty market data object
            return MarketData(
                symbol=instrument.symbol,
                current_price=Decimal("0"),
                last_updated=datetime.now()
            )

    @logfire.instrument("get_technical_data", extract_args=True)
    async def get_technical_data(self, symbol: str) -> Dict:
        """Get technical analysis data for a symbol."""
        try:
            self.logger.info(f"Fetching technical data for {symbol}")

            # Get multiple technical indicators
            indicators = {}

            # RSI
            rsi_data = await self.alpha_vantage.get_technical_indicators(symbol, "RSI")
            if rsi_data:
                latest_rsi = list(rsi_data.values())[0] if rsi_data else {}
                indicators["RSI"] = self._parse_decimal(latest_rsi.get("RSI"))

            # MACD
            macd_data = await self.alpha_vantage.get_technical_indicators(symbol, "MACD")
            if macd_data:
                latest_macd = list(macd_data.values())[0] if macd_data else {}
                indicators["MACD"] = {
                    "macd": self._parse_decimal(latest_macd.get("MACD")),
                    "signal": self._parse_decimal(latest_macd.get("MACD_Signal")),
                    "histogram": self._parse_decimal(latest_macd.get("MACD_Hist"))
                }

            # Moving Averages
            sma_20 = await self.alpha_vantage.get_technical_indicators(symbol, "SMA", time_period=20)
            sma_50 = await self.alpha_vantage.get_technical_indicators(symbol, "SMA", time_period=50)

            if sma_20:
                latest_sma20 = list(sma_20.values())[0] if sma_20 else {}
                indicators["SMA_20"] = self._parse_decimal(latest_sma20.get("SMA"))

            if sma_50:
                latest_sma50 = list(sma_50.values())[0] if sma_50 else {}
                indicators["SMA_50"] = self._parse_decimal(latest_sma50.get("SMA"))

            return indicators

        except Exception as e:
            self.logger.error(f"Error fetching technical data for {symbol}: {str(e)}")
            return {}

    @logfire.instrument("get_fundamental_data", extract_args=True)
    async def get_fundamental_data(self, symbol: str) -> Dict:
        """Get fundamental analysis data for a symbol."""
        try:
            self.logger.info(f"Fetching fundamental data for {symbol}")

            overview_data = await self.alpha_vantage.get_company_overview(symbol)

            return {
                "pe_ratio": self._parse_decimal(overview_data.get("pe_ratio")),
                "pb_ratio": self._parse_decimal(overview_data.get("pb_ratio")),
                "dividend_yield": self._parse_decimal(overview_data.get("dividend_yield")),
                "eps": self._parse_decimal(overview_data.get("eps")),
                "beta": self._parse_decimal(overview_data.get("beta")),
                "market_cap": self._parse_market_cap(overview_data.get("market_cap")),
                "sector": overview_data.get("sector"),
                "industry": overview_data.get("industry"),
                "description": overview_data.get("description", "")[:500],  # Truncate for context
            }

        except Exception as e:
            self.logger.error(f"Error fetching fundamental data for {symbol}: {str(e)}")
            return {}

    def _validate_market_data(self, quote_data: Dict, price_history: List, symbol: str) -> List[str]:
        """Validate market data quality and return list of issues."""
        issues = []

        # Check quote data
        if not quote_data:
            issues.append("No quote data available")
        elif quote_data.get("price", Decimal("0")) == Decimal("0"):
            issues.append("Quote price is zero or missing")

        # Check price history
        if not price_history:
            issues.append("No price history available")
        elif len(price_history) < 10:
            issues.append(f"Insufficient price history: only {len(price_history)} data points")

        # Check for recent price data
        if price_history:
            latest_date = max(price_history, key=lambda x: x.timestamp).timestamp
            days_old = (datetime.now() - latest_date).days
            if days_old > 7:
                issues.append(f"Price data is {days_old} days old")

        return issues

    async def _get_quote_with_fallback(self, symbol: str) -> Dict:
        """Get quote data with IB, YFinance fallback."""
        # Try Interactive Brokers first if enabled
        if self.ib_service:
            quote_data = await self.ib_service.get_stock_quote(symbol)
            if (quote_data and
                quote_data.get("price", Decimal("0")) != Decimal("0")):
                self.logger.info(f"Retrieved quote from Interactive Brokers for {symbol}")
                return quote_data

        # Try Alpha Vantage
        quote_data = await self.alpha_vantage.get_stock_quote(symbol)

        # Check if we got valid data
        if (quote_data and
            quote_data.get("price", Decimal("0")) != Decimal("0")):
            self.logger.info(f"Retrieved quote from Alpha Vantage for {symbol}")
            return quote_data

        # Fallback to YFinance
        self.logger.warning(f"Alpha Vantage quote failed for {symbol}, trying YFinance")
        fallback_data = await self.yfinance.get_stock_quote(symbol)

        if (fallback_data and
            fallback_data.get("price", Decimal("0")) != Decimal("0")):
            self.logger.info(f"Retrieved quote from YFinance fallback for {symbol}")
            return fallback_data

        self.logger.error(f"All quote sources failed for {symbol}")
        return {}

    async def _get_price_history_with_fallback(self, symbol: str, days: int) -> List:
        """Get price history with IB, YFinance fallback."""
        # Try Interactive Brokers first if enabled
        if self.ib_service:
            price_history = await self.ib_service.get_daily_prices(symbol, days)
            if price_history and len(price_history) >= 10:
                self.logger.info(f"Retrieved {len(price_history)} price points from Interactive Brokers for {symbol}")
                return price_history

        # Try Alpha Vantage
        price_history = await self.alpha_vantage.get_daily_prices(symbol, days)

        # Check if we got sufficient data
        if price_history and len(price_history) >= 10:
            self.logger.info(f"Retrieved {len(price_history)} price points from Alpha Vantage for {symbol}")
            return price_history

        # Fallback to YFinance
        self.logger.warning(f"Alpha Vantage price history insufficient for {symbol}, trying YFinance")
        fallback_data = await self.yfinance.get_daily_prices(symbol, days)

        if fallback_data and len(fallback_data) >= 10:
            self.logger.info(f"Retrieved {len(fallback_data)} price points from YFinance fallback for {symbol}")
            return fallback_data

        self.logger.error(f"All price history sources failed for {symbol}")
        return []

    async def _get_company_overview_with_fallback(self, symbol: str) -> Dict:
        """Get company overview with IB, YFinance fallback."""
        # Try Interactive Brokers first if enabled
        if self.ib_service:
            overview_data = await self.ib_service.get_company_overview(symbol)
            if overview_data and (overview_data.get("name") or overview_data.get("sector")):
                self.logger.info(f"Retrieved company overview from Interactive Brokers for {symbol}")
                return overview_data

        # Try Alpha Vantage
        overview_data = await self.alpha_vantage.get_company_overview(symbol)

        # Check if we got meaningful data
        if overview_data and (overview_data.get("name") or overview_data.get("sector")):
            self.logger.info(f"Retrieved company overview from Alpha Vantage for {symbol}")
            return overview_data

        # Fallback to YFinance (only for non-forex symbols)
        self.logger.warning(f"Alpha Vantage overview insufficient for {symbol}, trying YFinance")
        fallback_data = await self.yfinance.get_company_overview(symbol)

        if fallback_data and (fallback_data.get("name") or fallback_data.get("sector")):
            self.logger.info(f"Retrieved company overview from YFinance fallback for {symbol}")
            return fallback_data

        self.logger.debug(f"No company overview available for {symbol} (may be non-stock)")
        return {}

    async def _get_news_with_fallback(self, symbols: List[str], limit: int) -> List:
        """Get news with YFinance fallback."""
        # Try Alpha Vantage first
        news_items = await self.alpha_vantage.get_news_sentiment(symbols, limit)

        # Check if we got any news
        if news_items and len(news_items) > 0:
            self.logger.info(f"Retrieved {len(news_items)} news items from Alpha Vantage")
            return news_items

        # Fallback to YFinance
        self.logger.warning(f"Alpha Vantage news failed, trying YFinance")
        fallback_data = await self.yfinance.get_news_sentiment(symbols, limit)

        if fallback_data and len(fallback_data) > 0:
            self.logger.info(f"Retrieved {len(fallback_data)} news items from YFinance fallback")
            return fallback_data

        self.logger.warning(f"No news sources available for {symbols}")
        return []

    def _parse_decimal(self, value: Optional[str]) -> Optional[Decimal]:
        """Parse string value to Decimal."""
        if not value or value == "None" or value == "-":
            return None
        try:
            # Handle percentage values
            if isinstance(value, str) and value.endswith("%"):
                return Decimal(value[:-1]) / 100
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None

    def _parse_market_cap(self, value: Optional[str]) -> Optional[Decimal]:
        """Parse market cap string to Decimal."""
        if not value or value == "None":
            return None
        try:
            # Remove any non-numeric characters except decimal point
            clean_value = ''.join(c for c in str(value) if c.isdigit() or c == '.')
            return Decimal(clean_value) if clean_value else None
        except (ValueError, TypeError):
            return None

    async def close(self):
        """Close all service connections."""
        await self.alpha_vantage.close()
        await self.yfinance.close()
        if self.ib_service:
            await self.ib_service.close()