"""Test script for Interactive Brokers service integration."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nix_trader_ai.services.interactive_brokers_service import InteractiveBrokersService
from loguru import logger


async def test_connection():
    """Test basic connection to IB."""
    print("\n" + "="*60)
    print("TEST 1: Connection Test")
    print("="*60)

    ib_service = InteractiveBrokersService(
        host="127.0.0.1",
        port=7497,  # Paper trading port
        client_id=1
    )

    try:
        connected = ib_service.connect(timeout=10)
        if connected:
            print("✅ Successfully connected to Interactive Brokers")
            print(f"   Host: {ib_service.host}")
            print(f"   Port: {ib_service.port}")
            print(f"   Client ID: {ib_service.client_id}")
            print(f"   Next Order ID: {ib_service.wrapper.next_valid_order_id}")
            return ib_service
        else:
            print("❌ Failed to connect to Interactive Brokers")
            print("\nTroubleshooting:")
            print("1. Ensure TWS or IB Gateway is running")
            print("2. Check that API connections are enabled in TWS/Gateway settings")
            print("3. Verify the port number (7497 for paper, 7496 for live)")
            print("4. Check that the host IP is correct (127.0.0.1 for localhost)")
            return None
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return None


async def test_stock_quote(ib_service, symbol="AAPL"):
    """Test getting a stock quote."""
    print("\n" + "="*60)
    print(f"TEST 2: Stock Quote for {symbol}")
    print("="*60)

    try:
        quote = await ib_service.get_stock_quote(symbol)

        if quote and quote.get("price"):
            print(f"✅ Successfully retrieved quote for {symbol}")
            print(f"   Symbol: {quote.get('symbol')}")
            print(f"   Last Price: ${quote.get('price')}")
            print(f"   Bid: ${quote.get('bid')}")
            print(f"   Ask: ${quote.get('ask')}")
            print(f"   Change: ${quote.get('change')} ({quote.get('change_percent')})")
            print(f"   Volume: {quote.get('volume'):,}")
            print(f"   Date: {quote.get('latest_trading_day')}")
            return True
        else:
            print(f"❌ Failed to retrieve quote for {symbol}")
            print(f"   Response: {quote}")
            return False
    except Exception as e:
        print(f"❌ Error getting quote: {str(e)}")
        return False


async def test_historical_data(ib_service, symbol="AAPL", days=30):
    """Test getting historical price data."""
    print("\n" + "="*60)
    print(f"TEST 3: Historical Data for {symbol} ({days} days)")
    print("="*60)

    try:
        price_data = await ib_service.get_daily_prices(symbol, days)

        if price_data and len(price_data) > 0:
            print(f"✅ Successfully retrieved {len(price_data)} price bars")

            # Show first 5 and last 5 bars
            print("\n   First 5 bars:")
            for i, bar in enumerate(price_data[:5]):
                print(f"   [{i+1}] {bar.timestamp.strftime('%Y-%m-%d')} - "
                      f"O: ${bar.open_price:.2f}, H: ${bar.high_price:.2f}, "
                      f"L: ${bar.low_price:.2f}, C: ${bar.close_price:.2f}, "
                      f"V: {bar.volume:,}")

            if len(price_data) > 10:
                print("\n   Last 5 bars:")
                for i, bar in enumerate(price_data[-5:]):
                    print(f"   [{len(price_data)-4+i}] {bar.timestamp.strftime('%Y-%m-%d')} - "
                          f"O: ${bar.open_price:.2f}, H: ${bar.high_price:.2f}, "
                          f"L: ${bar.low_price:.2f}, C: ${bar.close_price:.2f}, "
                          f"V: {bar.volume:,}")

            # Calculate some basic stats
            if price_data:
                latest = price_data[0]
                oldest = price_data[-1]
                price_change = float(latest.close_price - oldest.close_price)
                pct_change = (price_change / float(oldest.close_price)) * 100

                print(f"\n   Period Statistics:")
                print(f"   Start Date: {oldest.timestamp.strftime('%Y-%m-%d')}")
                print(f"   End Date: {latest.timestamp.strftime('%Y-%m-%d')}")
                print(f"   Start Price: ${oldest.close_price:.2f}")
                print(f"   End Price: ${latest.close_price:.2f}")
                print(f"   Change: ${price_change:.2f} ({pct_change:+.2f}%)")

            return True
        else:
            print(f"❌ No historical data retrieved for {symbol}")
            return False
    except Exception as e:
        print(f"❌ Error getting historical data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_contract_details(ib_service, symbol="AAPL"):
    """Test getting contract/company details."""
    print("\n" + "="*60)
    print(f"TEST 4: Contract Details for {symbol}")
    print("="*60)

    try:
        details = await ib_service.get_company_overview(symbol)

        if details:
            print(f"✅ Successfully retrieved contract details for {symbol}")
            print(f"   Symbol: {details.get('symbol')}")
            print(f"   Name: {details.get('name')}")
            print(f"   Sector: {details.get('sector')}")
            print(f"   Industry: {details.get('industry')}")
            print(f"   Exchange: {details.get('exchange')}")
            print(f"   Currency: {details.get('currency')}")
            return True
        else:
            print(f"❌ No contract details retrieved for {symbol}")
            return False
    except Exception as e:
        print(f"❌ Error getting contract details: {str(e)}")
        return False


async def test_technical_indicators(ib_service, symbol="AAPL"):
    """Test calculating technical indicators."""
    print("\n" + "="*60)
    print(f"TEST 5: Technical Indicators for {symbol}")
    print("="*60)

    indicators = ["RSI", "SMA", "EMA", "MACD"]
    results = {}

    for indicator in indicators:
        try:
            print(f"\n   Calculating {indicator}...")

            if indicator in ["SMA", "EMA"]:
                data = await ib_service.get_technical_indicators(symbol, indicator, time_period=20)
            else:
                data = await ib_service.get_technical_indicators(symbol, indicator)

            if data:
                results[indicator] = data
                print(f"   ✅ {indicator}: {data}")
            else:
                print(f"   ❌ {indicator}: No data")
        except Exception as e:
            print(f"   ❌ {indicator}: Error - {str(e)}")

    if results:
        print(f"\n✅ Successfully calculated {len(results)}/{len(indicators)} indicators")
        return True
    else:
        print(f"\n❌ Failed to calculate any indicators")
        return False


async def test_multiple_symbols(ib_service, symbols=["AAPL", "MSFT", "GOOGL"]):
    """Test getting quotes for multiple symbols."""
    print("\n" + "="*60)
    print(f"TEST 6: Multiple Symbol Quotes")
    print("="*60)

    results = []

    for symbol in symbols:
        try:
            print(f"\n   Fetching {symbol}...")
            quote = await ib_service.get_stock_quote(symbol)

            if quote and quote.get("price"):
                print(f"   ✅ {symbol}: ${quote.get('price')} ({quote.get('change_percent')})")
                results.append(True)
            else:
                print(f"   ❌ {symbol}: No data")
                results.append(False)

            # Small delay to avoid overwhelming the API
            await asyncio.sleep(1)
        except Exception as e:
            print(f"   ❌ {symbol}: Error - {str(e)}")
            results.append(False)

    success_count = sum(results)
    print(f"\n✅ Successfully retrieved {success_count}/{len(symbols)} quotes")
    return success_count == len(symbols)


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Interactive Brokers Service Test Suite")
    print("="*60)
    print("\nPrerequisites:")
    print("1. TWS or IB Gateway must be running")
    print("2. API connections must be enabled")
    print("3. Port 7497 (paper trading) must be accessible")
    print("\nStarting tests in 3 seconds...")
    await asyncio.sleep(3)

    # Track test results
    test_results = {}

    # Test 1: Connection
    ib_service = await test_connection()
    test_results["Connection"] = ib_service is not None

    if not ib_service:
        print("\n" + "="*60)
        print("CRITICAL: Cannot proceed without IB connection")
        print("="*60)
        print("\nPlease ensure:")
        print("1. TWS or IB Gateway is running")
        print("2. In TWS/Gateway, go to: Edit > Global Configuration > API > Settings")
        print("3. Enable 'Enable ActiveX and Socket Clients'")
        print("4. Add '127.0.0.1' to 'Trusted IP Addresses' if needed")
        print("5. Set 'Socket port' to 7497 for paper trading")
        print("6. Restart TWS/Gateway after making changes")
        return

    # Test 2: Stock Quote
    test_results["Stock Quote"] = await test_stock_quote(ib_service, "AAPL")
    await asyncio.sleep(2)

    # Test 3: Historical Data
    test_results["Historical Data"] = await test_historical_data(ib_service, "AAPL", 30)
    await asyncio.sleep(2)

    # Test 4: Contract Details
    test_results["Contract Details"] = await test_contract_details(ib_service, "AAPL")
    await asyncio.sleep(2)

    # Test 5: Technical Indicators
    test_results["Technical Indicators"] = await test_technical_indicators(ib_service, "AAPL")
    await asyncio.sleep(2)

    # Test 6: Multiple Symbols
    test_results["Multiple Symbols"] = await test_multiple_symbols(ib_service, ["AAPL", "MSFT", "GOOGL"])

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<40} {status}")

    passed = sum(test_results.values())
    total = len(test_results)

    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)

    # Cleanup
    print("\nCleaning up...")
    ib_service.disconnect()
    print("Disconnected from IB")

    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)