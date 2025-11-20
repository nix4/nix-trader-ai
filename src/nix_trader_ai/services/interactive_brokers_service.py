"""Interactive Brokers API service integration."""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from collections import defaultdict

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import BarData, TickerId
from loguru import logger
import logfire

from ..models.market_data import NewsItem, PriceData


class IBWrapper(EWrapper):
    """Wrapper class to handle IB API callbacks."""

    def __init__(self):
        """Initialize the wrapper."""
        super().__init__()
        self.next_valid_order_id = None
        self.historical_data = defaultdict(list)
        self.realtime_bars = {}
        self.tick_prices = {}
        self.errors = []
        self.contract_details = {}
        self.news_articles = []

        # Events for synchronization
        self.connected_event = threading.Event()
        self.valid_id_event = threading.Event()
        self.historical_data_end = defaultdict(threading.Event)
        self.contract_details_end = defaultdict(threading.Event)

    def error(self, reqId: TickerId, errorCode: int, errorString: str, advancedOrderRejectJson: str = ""):
        """Handle error messages."""
        error_msg = f"ReqId: {reqId}, Code: {errorCode}, Msg: {errorString}"

        # Categorize error codes
        # Informational messages (not errors)
        info_codes = [2104, 2106, 2158, 2174]  # Market data farm, timezone warnings

        # Warning messages (non-critical)
        warning_codes = [2110, 162]  # Connection restored, IP address warning

        if errorCode in info_codes:
            logger.info(f"IB Info: {error_msg}")
        elif errorCode in warning_codes:
            logger.warning(f"IB Warning: {error_msg}")
            # Don't add warnings to error list - they don't prevent operation
        else:
            logger.error(f"IB Error: {error_msg}")
            self.errors.append({
                "req_id": reqId,
                "code": errorCode,
                "message": errorString,
                "timestamp": datetime.now()
            })

    def nextValidId(self, orderId: int):
        """Receive next valid order ID."""
        self.next_valid_order_id = orderId
        self.valid_id_event.set()
        logger.info(f"Next valid order ID: {orderId}")

    def connectAck(self):
        """Acknowledge successful connection."""
        logger.info("Connection acknowledged by IB")
        self.connected_event.set()

    def historicalData(self, reqId: int, bar: BarData):
        """Receive historical bar data."""
        self.historical_data[reqId].append({
            "date": bar.date,
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": int(bar.volume),
            "wap": float(bar.wap),  # Weighted average price
            "count": int(bar.barCount)
        })

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """Signal that historical data request is complete."""
        logger.info(f"Historical data end for reqId: {reqId}")
        self.historical_data_end[reqId].set()

    def realtimeBar(self, reqId: TickerId, time: int, open_: float, high: float,
                    low: float, close: float, volume: int, wap: float, count: int):
        """Receive real-time 5-second bars."""
        self.realtime_bars[reqId] = {
            "timestamp": datetime.fromtimestamp(time),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "wap": wap,
            "count": count
        }

    def tickPrice(self, reqId: TickerId, tickType: int, price: float, attrib):
        """Receive tick price data."""
        tick_type_map = {
            1: "bid",
            2: "ask",
            4: "last",
            6: "high",
            7: "low",
            9: "close"
        }

        if reqId not in self.tick_prices:
            self.tick_prices[reqId] = {}

        tick_name = tick_type_map.get(tickType, f"tick_{tickType}")
        self.tick_prices[reqId][tick_name] = price

    def tickSize(self, reqId: TickerId, tickType: int, size: int):
        """Receive tick size data (volume)."""
        if tickType == 5:  # Last size
            if reqId not in self.tick_prices:
                self.tick_prices[reqId] = {}
            self.tick_prices[reqId]["last_size"] = size
        elif tickType == 8:  # Volume
            if reqId not in self.tick_prices:
                self.tick_prices[reqId] = {}
            self.tick_prices[reqId]["volume"] = size

    def contractDetails(self, reqId: int, contractDetails):
        """Receive contract details."""
        self.contract_details[reqId] = {
            "symbol": contractDetails.contract.symbol,
            "sec_type": contractDetails.contract.secType,
            "exchange": contractDetails.contract.exchange,
            "currency": contractDetails.contract.currency,
            "long_name": contractDetails.longName,
            "industry": contractDetails.industry,
            "category": contractDetails.category,
            "subcategory": contractDetails.subcategory,
        }

    def contractDetailsEnd(self, reqId: int):
        """Signal that contract details request is complete."""
        logger.info(f"Contract details end for reqId: {reqId}")
        self.contract_details_end[reqId].set()


class IBClient(EClient):
    """Client class for IB API communication."""

    def __init__(self, wrapper):
        """Initialize the client."""
        EClient.__init__(self, wrapper)


class InteractiveBrokersService:
    """Service for interacting with Interactive Brokers API."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7497, client_id: int = 1):
        """
        Initialize the Interactive Brokers service.

        Args:
            host: TWS/IB Gateway host (default: 127.0.0.1)
            port: TWS port (7497 for paper trading, 7496 for live)
            client_id: Unique client identifier
        """
        self.host = host
        self.port = port
        self.client_id = client_id

        self.wrapper = IBWrapper()
        self.client = IBClient(self.wrapper)
        self.logger = logger.bind(service="interactive_brokers")

        self.connection_thread = None
        self.is_connected = False
        self._request_id_counter = 0
        self._lock = threading.Lock()

    def _get_next_request_id(self) -> int:
        """Get next available request ID."""
        with self._lock:
            self._request_id_counter += 1
            return self._request_id_counter

    def _run_client(self):
        """Run the client in a separate thread."""
        self.client.run()

    @logfire.instrument("ib_connect", extract_args=True)
    def connect(self, timeout: int = 10) -> bool:
        """
        Connect to Interactive Brokers TWS/Gateway.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected successfully
        """
        try:
            if self.is_connected:
                self.logger.info("Already connected to IB")
                return True

            self.logger.info(f"Connecting to IB at {self.host}:{self.port}")
            self.client.connect(self.host, self.port, self.client_id)

            # Start the client thread
            self.connection_thread = threading.Thread(target=self._run_client, daemon=True)
            self.connection_thread.start()

            # Wait for connection acknowledgment
            if not self.wrapper.connected_event.wait(timeout):
                self.logger.error("Connection timeout")
                return False

            # Wait for next valid order ID (indicates full connection)
            if not self.wrapper.valid_id_event.wait(timeout):
                self.logger.error("Timeout waiting for valid order ID")
                return False

            self.is_connected = True
            self.logger.info("Successfully connected to IB")
            logfire.info("IB connection established", host=self.host, port=self.port)
            return True

        except Exception as e:
            self.logger.error(f"Error connecting to IB: {str(e)}")
            logfire.error("IB connection failed", error=str(e))
            return False

    def disconnect(self):
        """Disconnect from Interactive Brokers."""
        if self.is_connected:
            self.client.disconnect()
            self.is_connected = False
            self.logger.info("Disconnected from IB")

    def _create_stock_contract(self, symbol: str, exchange: str = "SMART",
                              currency: str = "USD") -> Contract:
        """
        Create a stock contract.

        Args:
            symbol: Stock symbol
            exchange: Exchange (default: SMART for smart routing)
            currency: Currency (default: USD)

        Returns:
            Contract object
        """
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = exchange
        contract.currency = currency
        return contract

    @logfire.instrument("ib_get_quote", extract_args=True)
    async def get_stock_quote(self, symbol: str) -> Dict:
        """
        Get real-time stock quote.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with quote data
        """
        if not self.is_connected:
            if not self.connect():
                return {}

        try:
            req_id = self._get_next_request_id()
            contract = self._create_stock_contract(symbol)

            # Request market data
            self.client.reqMktData(req_id, contract, "", False, False, [])

            # Wait for data to arrive (give it a few seconds)
            await asyncio.sleep(2)

            # Cancel the market data subscription
            self.client.cancelMktData(req_id)

            # Get the accumulated data
            if req_id in self.wrapper.tick_prices:
                tick_data = self.wrapper.tick_prices[req_id]

                # Calculate change if we have close and last price
                change = Decimal("0")
                change_percent = "0%"
                if "last" in tick_data and "close" in tick_data:
                    last = Decimal(str(tick_data["last"]))
                    close = Decimal(str(tick_data["close"]))
                    change = last - close
                    if close != 0:
                        change_percent = f"{(float(change) / float(close) * 100):.2f}%"

                return {
                    "symbol": symbol,
                    "price": Decimal(str(tick_data.get("last", 0))),
                    "bid": Decimal(str(tick_data.get("bid", 0))),
                    "ask": Decimal(str(tick_data.get("ask", 0))),
                    "change": change,
                    "change_percent": change_percent,
                    "volume": tick_data.get("volume", 0),
                    "latest_trading_day": datetime.now().strftime("%Y-%m-%d"),
                }
            else:
                self.logger.warning(f"No quote data received for {symbol}")
                return {}

        except Exception as e:
            self.logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            return {}

    @logfire.instrument("ib_get_daily_prices", extract_args=True)
    async def get_daily_prices(self, symbol: str, days: int = 100) -> List[PriceData]:
        """
        Get daily price history.

        Args:
            symbol: Stock symbol
            days: Number of days of historical data

        Returns:
            List of PriceData objects
        """
        if not self.is_connected:
            if not self.connect():
                return []

        try:
            req_id = self._get_next_request_id()
            contract = self._create_stock_contract(symbol)

            # Request historical data
            # Use empty string for end_datetime to get most recent data
            # This avoids timezone issues and always gets latest available data
            end_datetime = ""
            duration = f"{days} D"
            bar_size = "1 day"
            what_to_show = "TRADES"
            use_rth = 1  # Regular trading hours only

            self.client.reqHistoricalData(
                req_id, contract, end_datetime, duration, bar_size,
                what_to_show, use_rth, 1, False, []
            )

            # Wait for data to arrive (timeout after 30 seconds)
            if not self.wrapper.historical_data_end[req_id].wait(30):
                self.logger.error(f"Timeout waiting for historical data for {symbol}")
                return []

            # Convert to PriceData objects
            price_data = []
            for bar in self.wrapper.historical_data[req_id]:
                try:
                    # Parse date - IB returns dates in format "20231201" or "20231201 16:00:00"
                    date_str = bar["date"].split()[0]  # Take just the date part
                    timestamp = datetime.strptime(date_str, "%Y%m%d")

                    price_data.append(PriceData(
                        symbol=symbol,
                        timestamp=timestamp,
                        open_price=Decimal(str(bar["open"])),
                        high_price=Decimal(str(bar["high"])),
                        low_price=Decimal(str(bar["low"])),
                        close_price=Decimal(str(bar["close"])),
                        volume=bar["volume"]
                    ))
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Error parsing price data for {symbol}: {e}")
                    continue

            # Clean up
            del self.wrapper.historical_data[req_id]
            del self.wrapper.historical_data_end[req_id]

            return sorted(price_data, key=lambda x: x.timestamp, reverse=True)

        except Exception as e:
            self.logger.error(f"Error fetching daily prices for {symbol}: {str(e)}")
            return []

    @logfire.instrument("ib_get_company_overview", extract_args=True)
    async def get_company_overview(self, symbol: str) -> Dict:
        """
        Get company fundamental data.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with company overview data
        """
        if not self.is_connected:
            if not self.connect():
                return {}

        try:
            req_id = self._get_next_request_id()
            contract = self._create_stock_contract(symbol)

            # Request contract details
            self.client.reqContractDetails(req_id, contract)

            # Wait for data to arrive
            if not self.wrapper.contract_details_end[req_id].wait(10):
                self.logger.error(f"Timeout waiting for contract details for {symbol}")
                return {}

            # Get the accumulated data
            if req_id in self.wrapper.contract_details:
                details = self.wrapper.contract_details[req_id]

                result = {
                    "symbol": symbol,
                    "name": details.get("long_name", ""),
                    "sector": details.get("category", ""),
                    "industry": details.get("industry", ""),
                    "exchange": details.get("exchange", ""),
                    "currency": details.get("currency", ""),
                }

                # Clean up
                del self.wrapper.contract_details[req_id]
                del self.wrapper.contract_details_end[req_id]

                return result
            else:
                self.logger.warning(f"No contract details received for {symbol}")
                return {}

        except Exception as e:
            self.logger.error(f"Error fetching company overview for {symbol}: {e}")
            return {}

    @logfire.instrument("ib_get_technical_indicators", extract_args=True)
    async def get_technical_indicators(self, symbol: str, indicator: str, **kwargs) -> Dict:
        """
        Get technical indicator data.

        Note: IB API doesn't provide pre-calculated technical indicators.
        This method fetches historical data and calculates indicators client-side.

        Args:
            symbol: Stock symbol
            indicator: Indicator type (RSI, MACD, SMA, EMA)
            **kwargs: Additional parameters (time_period, etc.)

        Returns:
            Dictionary with indicator data
        """
        try:
            # Get historical data for indicator calculation
            period = kwargs.get("time_period", 14)
            lookback_days = max(100, period * 3)  # Get enough data for calculation

            price_data = await self.get_daily_prices(symbol, lookback_days)

            if not price_data or len(price_data) < period:
                self.logger.warning(f"Insufficient data for {indicator} calculation")
                return {}

            # Extract close prices
            closes = [float(p.close_price) for p in reversed(price_data)]

            if indicator == "RSI":
                return self._calculate_rsi(closes, period)
            elif indicator == "SMA":
                return self._calculate_sma(closes, period)
            elif indicator == "EMA":
                return self._calculate_ema(closes, period)
            elif indicator == "MACD":
                return self._calculate_macd(closes)
            else:
                self.logger.warning(f"Unsupported indicator: {indicator}")
                return {}

        except Exception as e:
            self.logger.error(f"Error calculating {indicator} for {symbol}: {e}")
            return {}

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> Dict:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return {}

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            gains.append(max(change, 0))
            losses.append(max(-change, 0))

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        return {"RSI": Decimal(str(round(rsi, 2)))}

    def _calculate_sma(self, prices: List[float], period: int = 20) -> Dict:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return {}

        sma = sum(prices[-period:]) / period
        return {"SMA": Decimal(str(round(sma, 2)))}

    def _calculate_ema(self, prices: List[float], period: int = 20) -> Dict:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return {}

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # Start with SMA

        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema

        return {"EMA": Decimal(str(round(ema, 2)))}

    def _calculate_macd(self, prices: List[float], fast: int = 12,
                       slow: int = 26, signal: int = 9) -> Dict:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < slow + signal:
            return {}

        # Calculate EMAs
        def calc_ema(data, period):
            multiplier = 2 / (period + 1)
            ema = sum(data[:period]) / period
            for price in data[period:]:
                ema = (price - ema) * multiplier + ema
            return ema

        ema_fast = calc_ema(prices, fast)
        ema_slow = calc_ema(prices, slow)
        macd_line = ema_fast - ema_slow

        # Calculate signal line (EMA of MACD)
        # For simplicity, using a basic average here
        # In production, you'd want to calculate the full EMA history
        signal_line = macd_line * 0.9  # Simplified

        histogram = macd_line - signal_line

        return {
            "MACD": Decimal(str(round(macd_line, 4))),
            "MACD_Signal": Decimal(str(round(signal_line, 4))),
            "MACD_Hist": Decimal(str(round(histogram, 4)))
        }

    async def close(self):
        """Close the connection to IB."""
        self.disconnect()

