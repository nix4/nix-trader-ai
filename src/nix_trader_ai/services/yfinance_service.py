"""Yahoo Finance API service integration."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import yfinance as yf
from loguru import logger
import logfire

from ..models.market_data import NewsItem, PriceData


class YFinanceService:
    """Service for interacting with Yahoo Finance API."""

    def __init__(self):
        """Initialize the YFinance service."""
        self.logger = logger.bind(service="yfinance")

    @logfire.instrument("yfinance_get_quote", extract_args=True)
    async def get_stock_quote(self, symbol: str) -> Dict:
        """Get real-time stock quote from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")

            if hist.empty:
                self.logger.warning(f"No quote data available for {symbol}")
                return {}

            latest = hist.iloc[-1]

            # Calculate change if we have previous data
            change = Decimal("0")
            change_percent = "0%"
            if len(hist) > 1:
                previous = hist.iloc[-2]['Close']
                current = latest['Close']
                change = Decimal(str(current - previous))
                if previous != 0:
                    change_percent = f"{((current - previous) / previous * 100):.2f}%"

            return {
                "symbol": symbol,
                "price": Decimal(str(latest['Close'])),
                "change": change,
                "change_percent": change_percent,
                "volume": int(latest.get('Volume', 0)),
                "latest_trading_day": hist.index[-1].strftime("%Y-%m-%d"),
            }
        except Exception as e:
            self.logger.error(f"Error fetching quote for {symbol}: {e}")
            return {}

    @logfire.instrument("yfinance_get_daily_prices", extract_args=True)
    async def get_daily_prices(self, symbol: str, days: int = 100) -> List[PriceData]:
        """Get daily price history from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            # Get more data than needed to account for weekends/holidays
            period = "1y" if days > 252 else "6mo" if days > 126 else "3mo"
            hist = ticker.history(period=period)

            if hist.empty:
                self.logger.warning(f"No daily price data available for {symbol}")
                return []

            price_data = []
            for date, row in hist.tail(days).iterrows():
                try:
                    price_data.append(PriceData(
                        symbol=symbol,
                        timestamp=date.to_pydatetime().replace(tzinfo=None),
                        open_price=Decimal(str(row['Open'])),
                        high_price=Decimal(str(row['High'])),
                        low_price=Decimal(str(row['Low'])),
                        close_price=Decimal(str(row['Close'])),
                        volume=int(row.get('Volume', 0))
                    ))
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Error parsing price data for {symbol}: {e}")
                    continue

            return sorted(price_data, key=lambda x: x.timestamp, reverse=True)
        except Exception as e:
            self.logger.error(f"Error fetching daily prices for {symbol}: {e}")
            return []

    @logfire.instrument("yfinance_get_hourly_prices", extract_args=True)
    async def get_hourly_prices(self, symbol: str, hours: int = 24) -> List[PriceData]:
        """Get hourly price history from Yahoo Finance.

        Args:
            symbol: Trading symbol
            hours: Number of hours of data to fetch (max ~730 hours/~1 month)

        Returns:
            List of PriceData objects with hourly candles
        """
        try:
            ticker = yf.Ticker(symbol)

            # Determine period and interval based on hours requested
            # yfinance limits: 1h interval valid for max 730 days
            if hours <= 48:
                period = "2d"
            elif hours <= 168:  # 1 week
                period = "7d"
            elif hours <= 720:  # 1 month
                period = "1mo"
            else:
                period = "3mo"

            hist = ticker.history(period=period, interval="1h")

            if hist.empty:
                self.logger.warning(f"No hourly price data available for {symbol}")
                return []

            price_data = []
            for date, row in hist.tail(hours).iterrows():
                try:
                    price_data.append(PriceData(
                        symbol=symbol,
                        timestamp=date.to_pydatetime().replace(tzinfo=None),
                        open_price=Decimal(str(row['Open'])),
                        high_price=Decimal(str(row['High'])),
                        low_price=Decimal(str(row['Low'])),
                        close_price=Decimal(str(row['Close'])),
                        volume=int(row.get('Volume', 0))
                    ))
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Error parsing hourly price data for {symbol}: {e}")
                    continue

            return sorted(price_data, key=lambda x: x.timestamp, reverse=True)
        except Exception as e:
            self.logger.error(f"Error fetching hourly prices for {symbol}: {e}")
            return []

    @logfire.instrument("yfinance_get_company_overview", extract_args=True)
    async def get_company_overview(self, symbol: str) -> Dict:
        """Get company fundamental data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": str(info.get("marketCap", "")),
                "pe_ratio": str(info.get("trailingPE", "")),
                "pb_ratio": str(info.get("priceToBook", "")),
                "dividend_yield": str(info.get("dividendYield", "")),
                "eps": str(info.get("trailingEps", "")),
                "beta": str(info.get("beta", "")),
                "52_week_high": str(info.get("fiftyTwoWeekHigh", "")),
                "52_week_low": str(info.get("fiftyTwoWeekLow", "")),
                "description": info.get("longBusinessSummary", "")[:500],
            }
        except Exception as e:
            self.logger.error(f"Error fetching company overview for {symbol}: {e}")
            return {}

    @logfire.instrument("yfinance_get_news", extract_args=True)
    async def get_news_sentiment(self, symbols: List[str], limit: int = 20) -> List[NewsItem]:
        """Get news from Yahoo Finance."""
        news_items = []

        try:
            for symbol in symbols[:3]:  # Limit to avoid rate limiting
                try:
                    ticker = yf.Ticker(symbol)
                    news = ticker.news

                    for item in news[:limit//len(symbols) + 1]:
                        try:
                            # Convert timestamp to datetime
                            published_at = datetime.fromtimestamp(item.get("providerPublishTime", 0))

                            news_items.append(NewsItem(
                                title=item.get("title", ""),
                                content=item.get("summary", ""),
                                source=item.get("publisher", ""),
                                published_at=published_at,
                                url=item.get("link"),
                                symbols=[symbol],  # Yahoo Finance news is per symbol
                                sentiment_score=None  # Yahoo Finance doesn't provide sentiment
                            ))
                        except (ValueError, KeyError) as e:
                            self.logger.warning(f"Error parsing news item for {symbol}: {e}")
                            continue

                except Exception as e:
                    self.logger.warning(f"Error fetching news for {symbol}: {e}")
                    continue

            if news_items:
                # Sort by published date, most recent first
                news_items.sort(key=lambda x: x.published_at, reverse=True)
                return news_items[:limit]

        except Exception as e:
            self.logger.error(f"Error fetching news: {e}")

        return []

    async def close(self):
        """Close any resources (Yahoo Finance doesn't require cleanup)."""
        pass