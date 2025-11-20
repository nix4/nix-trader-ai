# Interactive Brokers Service Guide

## Overview

The Interactive Brokers (IB) service integration allows you to fetch real-time market data, historical prices, and calculate technical indicators directly from your local TWS (Trader Workstation) or IB Gateway instance.

## Prerequisites

### 1. TWS or IB Gateway Installation
- Download and install TWS or IB Gateway from [Interactive Brokers](https://www.interactivebrokers.com/)
- Use paper trading account for testing (recommended)

### 2. Enable API Access

In TWS/IB Gateway:
1. Go to **Edit** → **Global Configuration** → **API** → **Settings**
2. Check **"Enable ActiveX and Socket Clients"**
3. Add `127.0.0.1` to **"Trusted IP Addresses"** (or leave blank for localhost)
4. Set **Socket port**:
   - `7497` for paper trading (recommended for testing)
   - `7496` for live trading
5. Optionally, uncheck **"Read-Only API"** if you plan to place orders
6. Click **OK** and restart TWS/Gateway

### 3. Start TWS/Gateway
- Launch TWS or IB Gateway
- Log in with your credentials
- Ensure the application stays running while using the service

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Enable Interactive Brokers integration
ENABLE_IB=true

# IB Connection Settings
IB_HOST=127.0.0.1           # Localhost (default)
IB_PORT=7497                # 7497=paper trading, 7496=live
IB_CLIENT_ID=1              # Unique client ID (1-32)
```

### Important Notes

- **IB_PORT**: Use `7497` for paper trading, `7496` for live trading
- **IB_CLIENT_ID**: Each connection needs a unique ID (1-32). If you run multiple clients, increment this value.
- **ENABLE_IB**: Set to `false` to disable IB and use only Alpha Vantage/YFinance

## Testing the Service

Run the test script to verify your setup:

```bash
python test_ib_service.py
```

### Test Coverage

The test script validates:
1. **Connection**: Establishes connection to TWS/Gateway
2. **Stock Quote**: Retrieves real-time quote data
3. **Historical Data**: Fetches 30 days of daily price bars
4. **Contract Details**: Gets company/instrument information
5. **Technical Indicators**: Calculates RSI, SMA, EMA, MACD
6. **Multiple Symbols**: Tests concurrent symbol requests

### Expected Output

```
==============================================================
Interactive Brokers Service Test Suite
==============================================================

TEST 1: Connection Test
==============================================================
✅ Successfully connected to Interactive Brokers
   Host: 127.0.0.1
   Port: 7497
   Client ID: 1
   Next Order ID: 12345

TEST 2: Stock Quote for AAPL
==============================================================
✅ Successfully retrieved quote for AAPL
   Symbol: AAPL
   Last Price: $175.43
   Bid: $175.42
   Ask: $175.44
   Change: $2.15 (1.24%)
   Volume: 54,231,890
   Date: 2025-09-30

... (additional tests)

==============================================================
TEST SUMMARY
==============================================================
Connection................................. ✅ PASSED
Stock Quote................................ ✅ PASSED
Historical Data............................ ✅ PASSED
Contract Details........................... ✅ PASSED
Technical Indicators....................... ✅ PASSED
Multiple Symbols........................... ✅ PASSED

==============================================================
Results: 6/6 tests passed
==============================================================
```

## Using the Service Programmatically

### Direct Usage

```python
from nix_trader_ai.services.interactive_brokers_service import InteractiveBrokersService
import asyncio

async def main():
    # Initialize service
    ib_service = InteractiveBrokersService(
        host="127.0.0.1",
        port=7497,
        client_id=1
    )

    # Connect
    if not ib_service.connect():
        print("Failed to connect")
        return

    # Get quote
    quote = await ib_service.get_stock_quote("AAPL")
    print(f"AAPL: ${quote['price']}")

    # Get historical data
    prices = await ib_service.get_daily_prices("AAPL", days=30)
    print(f"Retrieved {len(prices)} price bars")

    # Get technical indicators
    rsi = await ib_service.get_technical_indicators("AAPL", "RSI")
    print(f"RSI: {rsi}")

    # Cleanup
    ib_service.disconnect()

asyncio.run(main())
```

### Through MarketDataService (Recommended)

The IB service is automatically integrated into the `MarketDataService` with fallback support:

```python
from nix_trader_ai.services.market_data_service import MarketDataService
from nix_trader_ai.models.instrument import TradingInstrument
from nix_trader_ai.models import InstrumentType
import asyncio

async def main():
    # Initialize market data service
    # IB will be used automatically if ENABLE_IB=true
    market_service = MarketDataService()

    # Create instrument
    instrument = TradingInstrument(
        symbol="AAPL",
        name="Apple Inc.",
        instrument_type=InstrumentType.STOCK,
        exchange="NASDAQ",
        currency="USD"
    )

    # Get market data (will try IB → Alpha Vantage → YFinance)
    market_data = await market_service.get_market_data(instrument)

    print(f"Symbol: {market_data.symbol}")
    print(f"Price: ${market_data.current_price}")
    print(f"Price History: {len(market_data.price_history)} bars")

    # Cleanup
    await market_service.close()

asyncio.run(main())
```

## API Methods

### Connection Management

#### `connect(timeout: int = 10) -> bool`
Establishes connection to TWS/Gateway.

**Returns**: `True` if connected successfully

**Example**:
```python
if ib_service.connect(timeout=10):
    print("Connected!")
```

#### `disconnect()`
Closes the connection.

**Example**:
```python
ib_service.disconnect()
```

### Market Data Methods

#### `async get_stock_quote(symbol: str) -> Dict`
Gets real-time stock quote.

**Parameters**:
- `symbol`: Stock ticker symbol (e.g., "AAPL")

**Returns**:
```python
{
    "symbol": "AAPL",
    "price": Decimal("175.43"),
    "bid": Decimal("175.42"),
    "ask": Decimal("175.44"),
    "change": Decimal("2.15"),
    "change_percent": "1.24%",
    "volume": 54231890,
    "latest_trading_day": "2025-09-30"
}
```

#### `async get_daily_prices(symbol: str, days: int = 100) -> List[PriceData]`
Gets historical daily price bars.

**Parameters**:
- `symbol`: Stock ticker symbol
- `days`: Number of days of history (default: 100)

**Returns**: List of `PriceData` objects with OHLCV data

**Example**:
```python
prices = await ib_service.get_daily_prices("AAPL", days=30)
for price in prices[:5]:
    print(f"{price.timestamp}: ${price.close_price}")
```

#### `async get_company_overview(symbol: str) -> Dict`
Gets company/contract details.

**Parameters**:
- `symbol`: Stock ticker symbol

**Returns**:
```python
{
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "exchange": "NASDAQ",
    "currency": "USD"
}
```

### Technical Indicators

#### `async get_technical_indicators(symbol: str, indicator: str, **kwargs) -> Dict`
Calculates technical indicators from historical data.

**Parameters**:
- `symbol`: Stock ticker symbol
- `indicator`: Indicator type ("RSI", "SMA", "EMA", "MACD")
- `time_period`: Period for calculation (default: 14 for RSI, 20 for SMA/EMA)

**Supported Indicators**:

**RSI (Relative Strength Index)**:
```python
rsi = await ib_service.get_technical_indicators("AAPL", "RSI", time_period=14)
# Returns: {"RSI": Decimal("65.43")}
```

**SMA (Simple Moving Average)**:
```python
sma = await ib_service.get_technical_indicators("AAPL", "SMA", time_period=20)
# Returns: {"SMA": Decimal("173.25")}
```

**EMA (Exponential Moving Average)**:
```python
ema = await ib_service.get_technical_indicators("AAPL", "EMA", time_period=20)
# Returns: {"EMA": Decimal("174.12")}
```

**MACD (Moving Average Convergence Divergence)**:
```python
macd = await ib_service.get_technical_indicators("AAPL", "MACD")
# Returns: {
#     "MACD": Decimal("1.2345"),
#     "MACD_Signal": Decimal("1.1111"),
#     "MACD_Hist": Decimal("0.1234")
# }
```

## Troubleshooting

### Connection Issues

**Problem**: `Connection timeout` or `Failed to connect`

**Solutions**:
1. Verify TWS/Gateway is running and logged in
2. Check API settings are enabled (see Prerequisites)
3. Verify correct port number in `.env`:
   - `7497` for paper trading
   - `7496` for live trading
4. Ensure no firewall is blocking localhost connections
5. Check TWS/Gateway logs for errors
6. Try restarting TWS/Gateway

### "Socket port is already in use"

**Problem**: Another application is using the port

**Solutions**:
1. Close other IB API clients
2. Change `IB_CLIENT_ID` to a different value (1-32)
3. Check TWS/Gateway → API → Active Clients to see connected clients
4. Restart TWS/Gateway if needed

### "Market data farm connection is broken"

**Problem**: IB data connection issue

**Solutions**:
1. This is often informational - wait a few seconds
2. Check your IB account has market data subscriptions
3. Verify you're logged into TWS/Gateway
4. For paper trading, ensure paper trading account is funded

### No Data Returned

**Problem**: Methods return empty dictionaries or lists

**Solutions**:
1. Check symbol is valid and traded on supported exchanges
2. Verify market is open or use previous close data
3. Check IB account has required market data permissions
4. Try a different symbol (e.g., "AAPL", "MSFT")
5. Review IB Gateway/TWS messages for errors

### "Requested market data is not subscribed"

**Problem**: Account lacks required market data subscription

**Solutions**:
1. For paper trading, this may be a temporary issue - try again
2. For live trading, check your IB account subscriptions
3. Subscribe to required market data feeds in Account Management

### "Trading TWS session is connected from a different IP address" (Code 162)

**Problem**: TWS detects connection from different IP than the logged-in session

**Solutions**:
1. This is a **warning**, not an error - the service will still work
2. To eliminate this warning:
   - In TWS/Gateway: **Edit** → **Global Configuration** → **API** → **Settings**
   - In **"Trusted IP Addresses"**, add `127.0.0.1` or leave blank
   - Check **"Allow connections from localhost only"** if available
   - Restart TWS/Gateway
3. If using VPN or proxy, ensure consistent connection
4. This warning doesn't affect functionality - you can ignore it

### "Date-time attributes without explicit time zone" (Code 2174)

**Problem**: Timezone warning for historical data requests

**Solutions**:
1. This is **informational only** - the service will work correctly
2. The service now uses empty end_datetime to get latest data (fixed)
3. This warning can be safely ignored - IB will use instrument's timezone
4. No action needed from your side

## Performance Considerations

### Connection Pooling
- The service maintains a single persistent connection
- Avoid creating multiple service instances
- Use the integrated `MarketDataService` for best practices

### Rate Limiting
- IB API has rate limits for data requests
- Add delays between requests when fetching multiple symbols:
  ```python
  for symbol in symbols:
      quote = await ib_service.get_stock_quote(symbol)
      await asyncio.sleep(1)  # 1 second delay
  ```

### Data Delays
- Real-time data may have 15-minute delay depending on subscriptions
- Paper trading accounts typically have delayed data
- Check your IB account's market data subscriptions

## Best Practices

1. **Always disconnect**: Use try/finally or context managers
   ```python
   try:
       ib_service.connect()
       # ... your code ...
   finally:
       ib_service.disconnect()
   ```

2. **Handle connection failures gracefully**:
   ```python
   if not ib_service.connect():
       # Fallback to other data sources
       quote = await alpha_vantage.get_stock_quote(symbol)
   ```

3. **Use the integrated MarketDataService**: Automatic fallback handling
   ```python
   # This handles IB → Alpha Vantage → YFinance fallback automatically
   market_service = MarketDataService()
   data = await market_service.get_market_data(instrument)
   ```

4. **Monitor for errors**: Check `wrapper.errors` for API errors
   ```python
   if ib_service.wrapper.errors:
       for error in ib_service.wrapper.errors:
           print(f"Error: {error['message']}")
   ```

5. **Test with paper trading first**: Always test with paper account before live

## Architecture Notes

### Threading Model
- IB API client runs in a separate daemon thread
- Main thread uses async/await for consistency with other services
- Thread-safe event synchronization for data callbacks

### Data Flow
```
User Request → InteractiveBrokersService
            ↓
    IB Client Thread (reqMktData/reqHistoricalData)
            ↓
    IB TWS/Gateway
            ↓
    IB Wrapper Callbacks (tickPrice/historicalData)
            ↓
    Event Signals Main Thread
            ↓
    Return Data to User
```

### Fallback Priority
When using `MarketDataService`:
1. **Interactive Brokers** (if enabled and connected)
2. **Alpha Vantage** (if IB fails or not enabled)
3. **Yahoo Finance** (if both above fail)

## Additional Resources

- [IB API Documentation](https://interactivebrokers.github.io/tws-api/)
- [IB Python API Guide](https://interactivebrokers.github.io/tws-api/introduction.html)
- [TWS API Reference](https://interactivebrokers.github.io/tws-api/classIBApi_1_1EClient.html)

## Support

For issues specific to:
- **IB Service Implementation**: Check this project's issues
- **IB API/TWS**: Contact Interactive Brokers support
- **Account/Permissions**: Log into IB Account Management