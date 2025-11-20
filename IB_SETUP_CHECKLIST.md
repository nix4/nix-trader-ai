# Interactive Brokers Setup Checklist

Quick setup guide to get your IB service running in 5 minutes.

## ☐ Step 1: Install IB Software (5 minutes)

### Download
- [ ] Go to https://www.interactivebrokers.com/
- [ ] Download **TWS** (full client) or **IB Gateway** (headless)
- [ ] Install the application

### Recommendation
- For development: **IB Gateway** (lighter, faster)
- For trading: **TWS** (full features)

---

## ☐ Step 2: Get Paper Trading Account (Already have one?)

### If you don't have an IB account:
- [ ] Sign up at https://www.interactivebrokers.com/
- [ ] Request paper trading account (free)
- [ ] Wait for approval (usually instant)

### If you have an IB account:
- [ ] Request paper trading access in Account Management
- [ ] Note your paper trading username

---

## ☐ Step 3: Configure TWS/Gateway API (2 minutes)

### Launch and Login
- [ ] Start TWS or IB Gateway
- [ ] Login with your credentials
- [ ] Select "Paper Trading" mode

### Enable API Access
- [ ] Go to: **Edit** → **Global Configuration** → **API** → **Settings**
- [ ] Check: **☑ Enable ActiveX and Socket Clients**
- [ ] Verify: **Socket port** is set to:
  - `7497` for paper trading ✅ (recommended)
  - `7496` for live trading
- [ ] Optional: Add `127.0.0.1` to "Trusted IP Addresses"
- [ ] Optional: Uncheck "Read-Only API" (if you want to place orders)
- [ ] Click **OK**
- [ ] **Restart TWS/Gateway** (important!)

---

## ☐ Step 4: Install Python Dependencies (30 seconds)

```bash
# Install the IB API library
pip install ibapi

# Or install all project dependencies
pip install -e .
```

---

## ☐ Step 5: Configure Environment Variables (1 minute)

### Edit your `.env` file:

```bash
# Enable Interactive Brokers integration
ENABLE_IB=true

# IB Connection Settings
IB_HOST=127.0.0.1
IB_PORT=7497              # Paper trading port
IB_CLIENT_ID=1            # Keep as 1 unless you have multiple clients
```

### Port Reference
- `7497` = Paper Trading (TWS)
- `7496` = Live Trading (TWS)
- `4002` = Paper Trading (IB Gateway)
- `4001` = Live Trading (IB Gateway)

---

## ☐ Step 6: Test the Connection (1 minute)

### Run the test script:
```bash
python test_ib_service.py
```

### Expected Output (if successful):
```
✅ Successfully connected to Interactive Brokers
   Host: 127.0.0.1
   Port: 7497
   Client ID: 1

✅ Successfully retrieved quote for AAPL
   Symbol: AAPL
   Last Price: $175.43
   ...

Results: 6/6 tests passed
```

### If it fails:
- Verify TWS/Gateway is running and logged in
- Check the API is enabled (Step 3)
- Verify port number matches (7497 for paper)
- Try restarting TWS/Gateway

---

## ☐ Step 7: Test in Your Code (optional)

Create a test file `test_my_ib.py`:

```python
from nix_trader_ai.services.interactive_brokers_service import InteractiveBrokersService
import asyncio

async def main():
    ib = InteractiveBrokersService(
        host="127.0.0.1",
        port=7497,
        client_id=1
    )

    if not ib.connect():
        print("❌ Connection failed")
        return

    print("✅ Connected!")

    # Get a quote
    quote = await ib.get_stock_quote("AAPL")
    print(f"AAPL: ${quote.get('price')}")

    ib.disconnect()
    print("✅ Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python test_my_ib.py
```

---

## Troubleshooting Quick Fixes

### ❌ "Couldn't connect to TWS"
**Fix**:
1. Is TWS/Gateway running? ➜ Start it
2. Did you enable API? ➜ See Step 3
3. Correct port? ➜ Check `.env` file
4. Restart TWS/Gateway ➜ Sometimes needed after config changes

### ❌ "Connection timeout"
**Fix**:
1. Check firewall isn't blocking localhost
2. Try a different CLIENT_ID (in `.env`, change IB_CLIENT_ID=2)
3. Check TWS/Gateway logs for errors

### ❌ "Socket port is already in use"
**Fix**:
1. Close other IB API clients
2. Go to TWS: **Help** → **API** → **Active Clients** and disconnect all
3. Change IB_CLIENT_ID in `.env` to a different number (1-32)

### ❌ "Market data not subscribed"
**Fix**:
1. For paper trading: Usually temporary, wait a minute
2. For live trading: Check account subscriptions in Account Management
3. Try a different symbol (e.g., "AAPL", "MSFT")

### ❌ Test script shows "0/6 tests passed"
**Fix**:
1. Complete all steps above ✅
2. Ensure TWS/Gateway shows "Connected" status
3. Try different symbols (some may not have data)
4. Check your paper trading account is active

### ⚠️ "Trading TWS session is connected from a different IP address"
**Note**: This is a **warning**, not an error
- The service will work fine - you can ignore this
- To eliminate: Add `127.0.0.1` to "Trusted IP Addresses" in TWS settings
- Not critical for functionality

### ℹ️ "Date-time attributes without explicit time zone"
**Note**: This is **informational only**
- Already fixed in the service (uses empty end_datetime)
- IB will use the instrument's timezone automatically
- No action needed - safe to ignore

---

## Verification Checklist

Before reporting issues, verify:

- [ ] TWS/IB Gateway is **running**
- [ ] You are **logged in** to paper trading
- [ ] API is **enabled** in settings
- [ ] Port number is **7497** (paper) or **7496** (live)
- [ ] TWS/Gateway was **restarted** after enabling API
- [ ] `.env` file has `ENABLE_IB=true`
- [ ] `.env` port matches TWS/Gateway port
- [ ] No other IB clients are using the same CLIENT_ID
- [ ] Test script runs without connection errors

---

## Quick Reference Card

| Item | Value |
|------|-------|
| Paper Trading Port (TWS) | 7497 |
| Live Trading Port (TWS) | 7496 |
| Paper Trading Port (Gateway) | 4002 |
| Live Trading Port (Gateway) | 4001 |
| Default Host | 127.0.0.1 |
| Client ID Range | 1-32 |
| Test Script | `python test_ib_service.py` |
| Documentation | `IB_SERVICE_GUIDE.md` |

---

## Next Steps After Setup

Once everything works:

1. **Read the Guide**: Review `IB_SERVICE_GUIDE.md` for detailed API documentation
2. **Check Examples**: See how to use in your trading agents
3. **Enable in Production**: Set `ENABLE_IB=true` in production `.env`
4. **Monitor Logs**: Watch for connection issues or rate limits
5. **Set Up Monitoring**: Configure alerts for connection failures

---

## Support

- **Setup Issues**: Review `IB_SERVICE_GUIDE.md` troubleshooting section
- **API Questions**: https://interactivebrokers.github.io/tws-api/
- **Account Issues**: Contact Interactive Brokers support
- **Code Issues**: Check project documentation

---

## ✅ All Done!

If all checks are complete, you're ready to use Interactive Brokers data in your trading system!

The service will automatically:
- Connect to TWS/Gateway when needed
- Fetch real-time market data
- Fall back to Alpha Vantage/YFinance if IB is unavailable
- Handle errors gracefully

**Happy Trading! 🚀**