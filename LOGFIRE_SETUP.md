# Logfire Telemetry Integration

The Nix Trader AI application includes comprehensive telemetry integration with [Logfire](https://logfire.pydantic.dev) for production monitoring, debugging, and observability.

## Features

### Automatic Instrumentation
- **HTTP requests** - All HTTP/HTTPX calls to external APIs are tracked
- **Async operations** - All asyncio operations are monitored
- **Pydantic models** - Model validation and serialization is traced
- **Custom spans** - Detailed tracing of trading analysis pipeline

### Monitored Components
- **Orchestrator workflows** - Screen instruments, analyze selections, full pipeline
- **AI Agent execution** - All 6 trading agents with execution time and context
- **Market data collection** - API calls to Alpha Vantage with response metadata
- **Technical analysis** - Support/resistance detection and indicator calculations
- **Error tracking** - Automatic error collection with context

## Setup Instructions

### 1. Get Logfire Token
1. Sign up at [logfire.pydantic.dev](https://logfire.pydantic.dev)
2. Create a new project
3. Copy your project token

### 2. Configure Environment
Add to your `.env` file:
```bash
# Logfire Configuration
LOGFIRE_TOKEN=your_token_here
LOGFIRE_SERVICE_NAME=nix-trader-ai
LOGFIRE_SERVICE_VERSION=0.1.0
LOGFIRE_ENVIRONMENT=production  # or development, staging
ENABLE_TELEMETRY=true
```

### 3. Verify Setup
Run the application and check your Logfire dashboard for:
- Traces showing the complete trading analysis pipeline
- Spans for each AI agent execution
- Metrics on analysis performance and success rates
- Error tracking with full context

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGFIRE_TOKEN` | None | Your Logfire project token |
| `LOGFIRE_SERVICE_NAME` | nix-trader-ai | Service identifier |
| `LOGFIRE_SERVICE_VERSION` | 0.1.0 | Version for tracking deployments |
| `LOGFIRE_ENVIRONMENT` | development | Environment name |
| `ENABLE_TELEMETRY` | true | Enable/disable telemetry |

## Monitored Metrics

### Performance Metrics
- Analysis pipeline execution time
- Individual agent response times
- Market data fetch latency
- Success/failure rates

### Business Metrics
- Number of instruments analyzed
- Recommendations generated
- Success scores and confidence levels
- Error rates by component

### Traces Include
- Complete request flow from start to finish
- AI agent prompts and responses (anonymized)
- Market data API calls and responses
- Error context with full stack traces

## Privacy & Security

- No sensitive data (API keys, personal info) is logged
- Trade recommendations are tracked by symbol only
- All data transmission uses HTTPS
- Retention follows Logfire's standard policies

## Troubleshooting

### No Data in Dashboard
1. Verify `LOGFIRE_TOKEN` is set correctly
2. Check `ENABLE_TELEMETRY=true`
3. Ensure network connectivity to Logfire
4. Check logs for "Logfire telemetry initialized successfully"

### Performance Impact
- Telemetry adds ~1-2ms overhead per operation
- Uses minimal memory (async batching)
- Can be disabled via `ENABLE_TELEMETRY=false`

## Development vs Production

### Development
- Uses local console logging + Logfire
- Detailed debug information
- More verbose spans

### Production
- Optimized telemetry collection
- Error-focused logging
- Performance monitoring