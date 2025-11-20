"""Main entry point for the Nix Trader AI application."""

import asyncio
from typing import List

import uvicorn
from loguru import logger

from .core.config import settings
from .core.orchestrator import TradingOrchestrator
from .models import TradingInstrument, InstrumentType
from .utils.logging_config import setup_logging


import logfire

logfire.configure()
logfire.instrument_pydantic_ai()
logfire.instrument_asyncpg()
logfire.instrument_httpx()  # Instrument HTTP requests (for Alpha Vantage API)
logfire.instrument_system_metrics()  # Track system performance 

async def main():
    """Main function for CLI usage with workflow options."""
    import sys

    # Setup logging
    setup_logging()
    logger.info("Starting Nix Trader AI")

    # Parse command line arguments for workflow control
    skip_screening = "--skip-screening" in sys.argv
    interactive_mode = "--interactive" in sys.argv

    # Get instruments from config
    instruments_config = settings.instruments
    instruments = [TradingInstrument(**instrument) for instrument in instruments_config]

    # Initialize orchestrator
    orchestrator = TradingOrchestrator()

    try:
        if interactive_mode:
            # Import and run interactive mode
            from .main_interactive import InteractiveTrader
            app = InteractiveTrader()
            await app.run()
            return

        if skip_screening:
            # Run direct analysis without screening
            logger.info("Running direct analysis (skipping screening)...")
            logger.info(f"Analyzing all {len(instruments)} favorite instruments")
            recommendations = await orchestrator.analyze_trading_opportunities(
                instruments, skip_screening=True
            )
        else:
            # Run full screening workflow (default)
            logger.info("Running full trading analysis with screening...")
            recommendations = await orchestrator.analyze_trading_opportunities(instruments)

        # Display results
        logger.info(f"Generated {len(recommendations)} trade recommendations:")

        if not recommendations:
            logger.warning("No trade recommendations were generated.")
            return

        for i, rec in enumerate(recommendations, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"RECOMMENDATION #{i}: {rec.symbol} - {rec.direction.upper()} {rec.timeframe.upper()}")
            logger.info(f"{'='*60}")
            logger.info(f"📊 Overall Score: {rec.overall_score}/100")
            logger.info(f"🔒 Confidence: {rec.confidence_level}%")
            logger.info(f"📈 Entry: ${rec.entry.price}")
            logger.info(f"🛑 Stop Loss: ${rec.exit.stop_loss} ({rec.exit.stop_loss_percent}%)")
            logger.info(f"🎯 Take Profit: ${rec.exit.take_profit[0] if rec.exit.take_profit else 'N/A'}")
            logger.info(f"⚖️  Risk/Reward: {rec.risk.risk_reward_ratio}:1")
            logger.info(f"💰 Position Size: {rec.risk.position_size_percent}%")

            # Display technical levels if available
            if rec.technical_analysis:
                if rec.technical_analysis.support_levels:
                    support_prices = [f"${level.price}" for level in rec.technical_analysis.support_levels[:2]]
                    logger.info(f"📉 Key Support: {', '.join(support_prices)}")
                if rec.technical_analysis.resistance_levels:
                    resistance_prices = [f"${level.price}" for level in rec.technical_analysis.resistance_levels[:2]]
                    logger.info(f"📈 Key Resistance: {', '.join(resistance_prices)}")

            logger.info(f"🔍 Key Factors: {', '.join(rec.key_factors[:2])}")
            logger.info(f"⚠️  Key Risks: {', '.join(rec.risks[:2])}")
            logger.info(f"💡 Reasoning: {rec.reasoning[:200]}...")

        logger.info(f"\n🎉 Analysis complete! {len(recommendations)} actionable recommendations generated.")

        # Show usage information
        logger.info(f"\n💡 Usage Tips:")
        logger.info(f"   Run with --skip-screening to analyze all instruments directly")
        logger.info(f"   Run with --interactive for interactive mode with instrument selection")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await orchestrator.close()


def start_api_server():
    """Start the FastAPI server."""
    setup_logging()
    logger.info("Starting Nix Trader AI API Server")

    uvicorn.run(
        "nix_trader_ai.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_config=None,  # Use our custom logging
    )


if __name__ == "__main__":
    # Run CLI version
    asyncio.run(main())