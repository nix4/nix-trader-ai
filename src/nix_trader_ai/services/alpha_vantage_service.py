"""Alpha Vantage API service integration."""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.alphaintelligence import AlphaIntelligence
from alpha_vantage.techindicators import TechIndicators
from loguru import logger
import logfire

from ..core.config import settings
from ..models.market_data import NewsItem, PriceData


class AlphaVantageService:
    """Service for interacting with Alpha Vantage API."""

    def __init__(self):
        """Initialize the Alpha Vantage service."""
        self.api_key = settings.alpha_vantage_api_key

        # Initialize Alpha Vantage Python library components
        self.ts = TimeSeries(key=self.api_key, output_format='json')
        self.fd = FundamentalData(key=self.api_key, output_format='json')
        self.ai = AlphaIntelligence(key=self.api_key, output_format='json')
        self.ti = TechIndicators(key=self.api_key, output_format='json')

        self.logger = logger.bind(service="alpha_vantage")

    @logfire.instrument("get_stock_quote", extract_args=True)
    async def get_stock_quote(self, symbol: str) -> Dict:
        """Get real-time stock quote."""
        try:
            # Use the Python library's quote endpoint
            data, _ = self.ts.get_quote_endpoint(symbol)

            quote = None
            if "Global Quote" in data:
                # Standard stock response format
                quote = data["Global Quote"]
            elif "01. symbol" in data:
                # Forex response format (direct key-value pairs)
                quote = data

            if quote:
                return {
                    "symbol": quote.get("01. symbol", symbol),
                    "price": Decimal(quote.get("05. price", "0")),
                    "change": Decimal(quote.get("09. change", "0")),
                    "change_percent": quote.get("10. change percent", "0%"),
                    "volume": int(quote.get("06. volume", 0)),
                    "latest_trading_day": quote.get("07. latest trading day"),
                }
            else:
                self.logger.warning(f"No quote data for {symbol}: {data}")
                return {}

        except Exception as e:
            self.logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return {}

    @logfire.instrument("get_daily_prices", extract_args=True)
    async def get_daily_prices(self, symbol: str, days: int = 100) -> List[PriceData]:
        """Get daily price history."""
        try:
            # Use the Python library's daily data endpoint
            outputsize = "compact" if days <= 100 else "full"
            data, _ = self.ts.get_daily(symbol, outputsize=outputsize)

            time_series = None
            if "Time Series (Daily)" in data:
                # Standard stock response format
                time_series = data["Time Series (Daily)"]
            else:
                # Check if it's a direct time series response (forex format)
                # Look for date keys in the data
                for key in data.keys():
                    # Check if key looks like a date (YYYY-MM-DD format)
                    if len(key) == 10 and key.count('-') == 2:
                        try:
                            datetime.strptime(key, "%Y-%m-%d")
                            # If we found a date key, the whole data dict is the time series
                            time_series = data
                            break
                        except ValueError:
                            continue

            if not time_series:
                self.logger.warning(f"No daily data for {symbol}: {data}")
                return []

            price_data = []
            for date_str, values in list(time_series.items())[:days]:
                try:
                    # Skip non-date keys that might be in the response
                    if len(date_str) != 10 or date_str.count('-') != 2:
                        continue

                    price_data.append(PriceData(
                        symbol=symbol,
                        timestamp=datetime.strptime(date_str, "%Y-%m-%d"),
                        open_price=Decimal(values["1. open"]),
                        high_price=Decimal(values["2. high"]),
                        low_price=Decimal(values["3. low"]),
                        close_price=Decimal(values["4. close"]),
                        volume=int(values.get("5. volume", 0))  # Forex might not have volume
                    ))
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Error parsing price data for {symbol} on {date_str}: {e}")
                    continue

            return sorted(price_data, key=lambda x: x.timestamp, reverse=True)

        except Exception as e:
            self.logger.error(f"Error fetching daily prices for {symbol}: {str(e)}")
            return []

    @logfire.instrument("get_company_overview", extract_args=True)
    async def get_company_overview(self, symbol: str) -> Dict:
        """Get company fundamental data."""
        # Skip company overview for non-stock instruments (forex, crypto, etc.)
        if self._is_non_stock_symbol(symbol):
            self.logger.debug(f"Skipping company overview for non-stock symbol: {symbol}")
            return {}

        try:
            # Use the Python library's company overview endpoint
            data, _ = self.fd.get_company_overview(symbol)

            if "Symbol" in data:
                return {
                    "symbol": data.get("Symbol"),
                    "name": data.get("Name"),
                    "sector": data.get("Sector"),
                    "industry": data.get("Industry"),
                    "market_cap": data.get("MarketCapitalization"),
                    "pe_ratio": data.get("PERatio"),
                    "pb_ratio": data.get("PriceToBookRatio"),
                    "dividend_yield": data.get("DividendYield"),
                    "eps": data.get("EPS"),
                    "beta": data.get("Beta"),
                    "52_week_high": data.get("52WeekHigh"),
                    "52_week_low": data.get("52WeekLow"),
                    "description": data.get("Description"),
                }
            else:
                self.logger.debug(f"No overview data for {symbol}: {data}")
                return {}

        except Exception as e:
            self.logger.warning(f"Error fetching overview for {symbol}: {str(e)}")
            return {}

    def _is_non_stock_symbol(self, symbol: str) -> bool:
        """Check if symbol is likely a non-stock instrument."""
        symbol_upper = symbol.upper()

        # Common currencies
        currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD',
            'CNY', 'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'RUB'
        ]

        # Precious metals and commodities (often traded against USD)
        commodities = [
            'XAU',  # Gold
            'XAG',  # Silver
            'XPT',  # Platinum
            'XPD',  # Palladium
            'GOLD', 'SILVER', 'OIL', 'GAS', 'COPPER', 'WTI', 'BRENT'
        ]

        # Check for forex pairs (e.g., GBPUSD, EURUSD)
        if len(symbol_upper) == 6:
            base = symbol_upper[:3]
            quote = symbol_upper[3:]
            if (base in currencies and quote in currencies) or \
               (base in commodities and quote in currencies):
                return True

        # Check for other forex/commodity formats with separators
        separators = ['/', '-', '_']
        for sep in separators:
            if sep in symbol_upper:
                parts = symbol_upper.split(sep)
                if len(parts) == 2:
                    base, quote = parts
                    if (base in currencies and quote in currencies) or \
                       (base in commodities and quote in currencies):
                        return True

        # Common crypto patterns
        crypto_patterns = ['BTC', 'ETH', 'LTC', 'XRP', 'ADA', 'DOT', 'DOGE', 'USDT', 'USDC', 'MATIC', 'LINK']
        if any(crypto in symbol_upper for crypto in crypto_patterns):
            return True

        # Additional commodity patterns
        if any(commodity in symbol_upper for commodity in commodities):
            return True

        # Common forex/CFD suffixes
        if symbol_upper.endswith(('USD', 'EUR', 'GBP', 'JPY')):
            # Check if it looks like a forex pair
            base_part = symbol_upper[:-3]
            if len(base_part) == 3 and (base_part in currencies or base_part in commodities):
                return True

        return False

    @logfire.instrument("get_news_sentiment", extract_args=True)
    async def get_news_sentiment(self, symbols: List[str], limit: int = 20) -> List[NewsItem]:
        """Get news and sentiment data with fallback to Yahoo Finance."""
        if not symbols:
            return []

        # First try Alpha Vantage using the Python library
        try:
            tickers = ",".join(symbols[:5])  # API limit
            data, _ = self.ai.get_news_sentiment(tickers=tickers, limit=limit)

            if "feed" in data and data["feed"]:
                news_items = []
                for item in data["feed"]:
                    try:
                        # Parse sentiment score
                        sentiment_score = None
                        if "overall_sentiment_score" in item:
                            sentiment_score = float(item["overall_sentiment_score"])

                        # Parse time_published
                        published_at = datetime.now()
                        if item.get("time_published"):
                            time_str = item["time_published"]
                            # Handle different time formats from Alpha Vantage
                            if "T" in time_str:
                                time_str = time_str.replace("T", " ").replace("Z", "")
                            try:
                                published_at = datetime.fromisoformat(time_str)
                            except ValueError:
                                # Try parsing without microseconds
                                try:
                                    published_at = datetime.strptime(time_str[:19], "%Y%m%d %H%M%S")
                                except ValueError:
                                    self.logger.warning(f"Could not parse time: {time_str}")

                        news_items.append(NewsItem(
                            title=item.get("title", ""),
                            content=item.get("summary", ""),
                            source=item.get("source", ""),
                            published_at=published_at,
                            url=item.get("url"),
                            symbols=[ticker["ticker"] for ticker in item.get("ticker_sentiment", [])],
                            sentiment_score=sentiment_score
                        ))
                    except (ValueError, KeyError) as e:
                        self.logger.warning(f"Error parsing Alpha Vantage news item: {e}")
                        continue

                if news_items:
                    self.logger.info(f"Retrieved {len(news_items)} news items from Alpha Vantage")
                    return news_items[:limit]

        except Exception as e:
            self.logger.warning(f"Alpha Vantage news fetch failed: {str(e)}, falling back to Yahoo Finance")

        return []

    @logfire.instrument("get_technical_indicators", extract_args=True)
    async def get_technical_indicators(self, symbol: str, indicator: str, **kwargs) -> Dict:
        """Get technical indicator data."""
        # Map indicator names to TechIndicators methods
        indicator_methods = {
            "RSI": "get_rsi",
            "MACD": "get_macd",
            "SMA": "get_sma",
            "EMA": "get_ema",
            "BBANDS": "get_bbands",
            "ADX": "get_adx"
        }

        if indicator not in indicator_methods:
            raise ValueError(f"Unsupported indicator: {indicator}")

        try:
            # Get the method from TechIndicators class
            method = getattr(self.ti, indicator_methods[indicator])

            # Prepare parameters
            interval = kwargs.get("interval", "daily")
            time_period = kwargs.get("time_period", 14)
            series_type = kwargs.get("series_type", "close")

            # Call the appropriate method based on indicator type
            if indicator == "MACD":
                data, _ = method(symbol, interval=interval, series_type=series_type)
            elif indicator == "BBANDS":
                data, _ = method(symbol, interval=interval, time_period=time_period, series_type=series_type)
            else:
                data, _ = method(symbol, interval=interval, time_period=time_period, series_type=series_type)

            # Find the technical analysis key (varies by indicator)
            tech_key = None
            for key in data.keys():
                if "Technical Analysis" in key:
                    tech_key = key
                    break

            if tech_key and tech_key in data:
                return data[tech_key]
            else:
                self.logger.warning(f"No technical data for {symbol} {indicator}: {data}")
                return {}

        except Exception as e:
            self.logger.error(f"Error fetching {indicator} for {symbol}: {str(e)}")
            return {}

    async def close(self):
        """Close any resources (no longer needed since we use the Python library)."""
        pass