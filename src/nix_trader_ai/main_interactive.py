"""Interactive main entry point for the Nix Trader AI application."""

import asyncio
from typing import List

from loguru import logger

from .core.config import settings
from .core.orchestrator import TradingOrchestrator
from .models import TradingInstrument, InstrumentType
from .utils.logging_config import setup_logging


class InteractiveTrader:
    """Interactive trading application interface."""

    def __init__(self):
        """Initialize the interactive trader."""
        setup_logging()
        self.orchestrator = TradingOrchestrator()
        self.favorite_instruments = [
            TradingInstrument(**instrument) for instrument in settings.instruments
        ]

    async def run(self):
        """Run the interactive trading application."""
        try:
            logger.info("🚀 Welcome to Nix Trader AI - Interactive Trading Assistant")
            logger.info("=" * 60)

            while True:
                choice = await self._show_main_menu()

                if choice == "1":
                    await self._run_screening_workflow()
                elif choice == "2":
                    await self._run_direct_analysis()
                elif choice == "3":
                    await self._show_favorite_instruments()
                elif choice == "4":
                    await self._show_market_overview()
                elif choice == "5":
                    logger.info("👋 Thank you for using Nix Trader AI!")
                    break
                else:
                    logger.warning("❌ Invalid choice. Please try again.")

                input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            logger.info("\n👋 Application interrupted by user.")
        finally:
            await self.orchestrator.close()

    async def _show_main_menu(self) -> str:
        """Display the main menu and get user choice."""
        print("\n" + "=" * 60)
        print("📊 NIX TRADER AI - MAIN MENU")
        print("=" * 60)
        print("1. 🔍 Run Screening Workflow (Screen + Select + Analyze)")
        print("2. ⚡ Direct Analysis (Skip Screening)")
        print("3. 📋 View Favorite Instruments")
        print("4. 📈 Market Overview")
        print("5. 🚪 Exit")
        print("=" * 60)

        choice = input("Select an option (1-5): ").strip()
        return choice

    async def _run_screening_workflow(self):
        """Run the full screening workflow."""
        logger.info("🔍 Starting Screening Workflow...")

        # Step 1: Run screening
        print("\n📊 Screening favorite instruments for best opportunities...")
        screening_results = await self.orchestrator.screen_instruments(self.favorite_instruments)

        market_overview = screening_results["market_overview"]
        recommended_instruments = screening_results["recommended_instruments"]

        # Step 2: Display screening results
        print("\n" + "=" * 50)
        print("🎯 SCREENING RESULTS")
        print("=" * 50)

        print("\n📈 Market Overview:")
        for symbol, data in market_overview.items():
            print(f"  {symbol}: Price: ${data.get('current_price', 'N/A')}, "
                  f"Volume: {data.get('volume', 'N/A')}, "
                  f"Volatility: {data.get('volatility', 'N/A')}")

        print(f"\n🏆 Recommended Instruments ({len(recommended_instruments)}):")
        for i, instrument in enumerate(recommended_instruments, 1):
            print(f"  {i}. {instrument.symbol} - {instrument.name}")

        # Step 3: User selection
        selected_instruments = await self._select_instruments_for_analysis(recommended_instruments)

        if not selected_instruments:
            logger.warning("❌ No instruments selected for analysis.")
            return

        # Step 4: Run detailed analysis
        await self._run_analysis_on_instruments(selected_instruments)

    async def _run_direct_analysis(self):
        """Run direct analysis without screening."""
        logger.info("⚡ Starting Direct Analysis...")

        print("\n📋 Available instruments for analysis:")
        for i, instrument in enumerate(self.favorite_instruments, 1):
            print(f"  {i}. {instrument.symbol} - {instrument.name}")

        # User selection
        selected_instruments = await self._select_instruments_for_analysis(self.favorite_instruments)

        if not selected_instruments:
            logger.warning("❌ No instruments selected for analysis.")
            return

        # Run analysis
        await self._run_analysis_on_instruments(selected_instruments)

    async def _select_instruments_for_analysis(
        self, available_instruments: List[TradingInstrument]
    ) -> List[TradingInstrument]:
        """Allow user to select instruments for analysis."""
        print(f"\n🎯 Select instruments to analyze (1-{len(available_instruments)}):")
        print("Enter numbers separated by commas (e.g., 1,2,3) or 'all' for all instruments:")

        selection = input("Your selection: ").strip().lower()

        if selection == "all":
            return available_instruments

        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            selected = [available_instruments[i] for i in indices if 0 <= i < len(available_instruments)]

            if not selected:
                print("❌ No valid selections made.")
                return []

            print(f"\n✅ Selected {len(selected)} instruments:")
            for instrument in selected:
                print(f"  • {instrument.symbol} - {instrument.name}")

            return selected

        except (ValueError, IndexError):
            print("❌ Invalid selection format. Please try again.")
            return []

    async def _run_analysis_on_instruments(self, instruments: List[TradingInstrument]):
        """Run detailed analysis on selected instruments."""
        print(f"\n🔬 Running comprehensive analysis on {len(instruments)} instruments...")
        print("⏳ This may take a few minutes as we consult our AI agents...")

        # Run the analysis
        recommendations = await self.orchestrator.analyze_selected_instruments(instruments)

        # Display results
        await self._display_trade_recommendations(recommendations)

    async def _display_trade_recommendations(self, recommendations: List):
        """Display the trade recommendations."""
        print("\n" + "=" * 80)
        print("💡 TRADE RECOMMENDATIONS")
        print("=" * 80)

        if not recommendations:
            print("❌ No trade recommendations generated.")
            return

        for i, rec in enumerate(recommendations, 1):
            print(f"\n🔥 RECOMMENDATION #{i}")
            print("-" * 40)
            print(f"📊 Symbol: {rec.symbol}")
            print(f"📈 Direction: {rec.direction.upper()}")
            print(f"⏱️  Timeframe: {rec.timeframe.upper()}")
            print(f"🎯 Overall Score: {rec.overall_score}/100")
            print(f"🔒 Confidence: {rec.confidence_level}%")

            print(f"\n💰 TRADE DETAILS:")
            print(f"  📈 Entry Price: ${rec.entry.price}")
            print(f"  🛑 Stop Loss: ${rec.exit.stop_loss} ({rec.exit.stop_loss_percent}%)")
            print(f"  🎯 Take Profit: ${rec.exit.take_profit[0]} ({rec.exit.take_profit_percents[0]}%)")

            print(f"\n⚖️  RISK ANALYSIS:")
            print(f"  Risk/Reward: {rec.risk.risk_reward_ratio}:1")
            print(f"  Position Size: {rec.risk.position_size_percent}%")
            print(f"  Risk Level: {rec.risk.risk_level.upper()}")

            print(f"\n🔍 KEY FACTORS:")
            for factor in rec.key_factors[:3]:  # Show top 3
                print(f"  • {factor}")

            print(f"\n⚠️  RISKS TO MONITOR:")
            for risk in rec.risks[:2]:  # Show top 2
                print(f"  • {risk}")

            if rec.technical_analysis:
                print(f"\n📊 TECHNICAL LEVELS:")
                if rec.technical_analysis.support_levels:
                    support_prices = [f"${level.price}" for level in rec.technical_analysis.support_levels[:2]]
                    print(f"  📉 Support: {', '.join(support_prices)}")
                if rec.technical_analysis.resistance_levels:
                    resistance_prices = [f"${level.price}" for level in rec.technical_analysis.resistance_levels[:2]]
                    print(f"  📈 Resistance: {', '.join(resistance_prices)}")

        print(f"\n🎉 Analysis Complete! Generated {len(recommendations)} trade recommendations.")

    async def _show_favorite_instruments(self):
        """Display favorite instruments."""
        print("\n" + "=" * 50)
        print("📋 FAVORITE INSTRUMENTS")
        print("=" * 50)

        for i, instrument in enumerate(self.favorite_instruments, 1):
            print(f"{i}. {instrument.symbol} - {instrument.name}")
            print(f"   Type: {instrument.instrument_type.title()}")
            print(f"   Exchange: {instrument.exchange or 'N/A'}")
            print(f"   Sector: {instrument.sector or 'N/A'}")
            print()

    async def _show_market_overview(self):
        """Display market overview for favorite instruments."""
        print("\n📈 Fetching market overview...")

        market_data = {}
        for instrument in self.favorite_instruments:
            try:
                data = await self.orchestrator.market_data_service.get_market_data(instrument)
                market_data[instrument.symbol] = {
                    "price": data.current_price,
                    "volume": data.volume_24h,
                    "news": len(data.news_items)
                }
            except Exception as e:
                logger.warning(f"Error fetching data for {instrument.symbol}: {e}")
                market_data[instrument.symbol] = {"price": "N/A", "volume": "N/A", "news": 0}

        print("\n" + "=" * 60)
        print("📊 MARKET OVERVIEW")
        print("=" * 60)
        print(f"{'Symbol':<10} {'Price':<12} {'Volume':<15} {'News':<8}")
        print("-" * 60)

        for symbol, data in market_data.items():
            price_str = f"${data['price']}" if data['price'] != "N/A" else "N/A"
            volume_str = str(data['volume']) if data['volume'] != "N/A" else "N/A"
            news_str = str(data['news'])
            print(f"{symbol:<10} {price_str:<12} {volume_str:<15} {news_str:<8}")


async def main():
    """Main entry point for interactive trading application."""
    app = InteractiveTrader()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())