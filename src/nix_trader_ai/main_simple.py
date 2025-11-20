"""Simple demonstration of the trading framework without AI agents."""

import asyncio
from datetime import datetime
from decimal import Decimal

from nix_trader_ai.models import TradingInstrument, InstrumentType
from nix_trader_ai.models.analysis import TechnicalAnalysis, AnalysisSignal, SupportResistanceLevel
from nix_trader_ai.models.trade import TradeRecommendation, TradeDirection, TradeTimeframe, TradeEntry, TradeExit, TradeRisk
from nix_trader_ai.utils.logging_config import setup_logging
from nix_trader_ai.utils.technical_indicators import TechnicalAnalyzer
from nix_trader_ai.models.market_data import PriceData

from loguru import logger


def create_sample_price_data(symbol: str) -> list:
    """Create sample price data for demonstration."""
    import random

    base_price = 150.0
    price_data = []

    for i in range(100):
        # Simple random walk
        change = random.uniform(-0.02, 0.02)
        base_price *= (1 + change)

        price_data.append(PriceData(
            symbol=symbol,
            timestamp=datetime.now(),
            open_price=Decimal(str(base_price * 0.999)),
            high_price=Decimal(str(base_price * 1.005)),
            low_price=Decimal(str(base_price * 0.995)),
            close_price=Decimal(str(base_price)),
            volume=random.randint(1000000, 5000000)
        ))

    return price_data


def create_sample_technical_analysis(symbol: str, price_data: list) -> TechnicalAnalysis:
    """Create sample technical analysis using our S/R detection."""
    # Use our technical analyzer
    analyzer = TechnicalAnalyzer()

    # Find support and resistance levels
    sr_levels = analyzer.find_support_resistance_levels(price_data)

    # Convert to our Pydantic models
    support_levels = [
        SupportResistanceLevel(
            price=level.price,
            level_type=level.level_type,
            strength=level.strength,
            touches=level.touches
        ) for level in sr_levels["support"]
    ]

    resistance_levels = [
        SupportResistanceLevel(
            price=level.price,
            level_type=level.level_type,
            strength=level.strength,
            touches=level.touches
        ) for level in sr_levels["resistance"]
    ]

    # Calculate Fibonacci levels
    fib_levels = analyzer.calculate_fibonacci_levels(price_data)

    # Identify chart patterns
    patterns = analyzer.identify_chart_patterns(price_data)

    return TechnicalAnalysis(
        symbol=symbol,
        indicators=[],
        support_levels=support_levels,
        resistance_levels=resistance_levels,
        fibonacci_levels=fib_levels,
        chart_patterns=[],
        trend_direction=patterns[0]["type"] if patterns else "sideways",
        trend_strength=patterns[0]["strength"] if patterns else 0.5,
        key_levels={
            "nearest_support": support_levels[0].price if support_levels else Decimal("145.0"),
            "nearest_resistance": resistance_levels[0].price if resistance_levels else Decimal("155.0")
        },
        signal=AnalysisSignal.BUY,
        score=75.0,
        reasoning="Strong support levels detected with bullish momentum indicators.",
        analyzed_at=datetime.now()
    )


def create_sample_trade_recommendation(symbol: str, technical_analysis: TechnicalAnalysis) -> TradeRecommendation:
    """Create a sample trade recommendation using S/R levels."""
    current_price = Decimal("150.00")

    # Use nearest support for stop loss
    stop_loss = technical_analysis.key_levels.get("nearest_support", Decimal("145.0"))

    # Use nearest resistance for take profit
    take_profit = technical_analysis.key_levels.get("nearest_resistance", Decimal("155.0"))

    # Calculate risk-reward
    risk = float(current_price - stop_loss)
    reward = float(take_profit - current_price)
    risk_reward_ratio = Decimal(str(reward / risk)) if risk > 0 else Decimal("0")

    return TradeRecommendation(
        symbol=symbol,
        direction=TradeDirection.LONG,
        timeframe=TradeTimeframe.SWING,
        entry=TradeEntry(
            price=current_price,
            quantity=100,
            order_type="limit",
            confidence=85.0
        ),
        exit=TradeExit(
            stop_loss=stop_loss,
            take_profit=[take_profit],
            stop_loss_percent=Decimal(str((float(current_price - stop_loss) / float(current_price)) * 100)),
            take_profit_percents=[Decimal(str((float(take_profit - current_price) / float(current_price)) * 100))]
        ),
        risk=TradeRisk(
            risk_reward_ratio=risk_reward_ratio,
            position_size_percent=Decimal("3.0"),
            max_loss_amount=Decimal(str(risk * 100)),
            max_gain_amount=Decimal(str(reward * 100)),
            probability_of_success=0.75,
            risk_level="medium"
        ),
        technical_analysis=technical_analysis,
        overall_score=80.0,
        confidence_level=85.0,
        reasoning=f"""
        Strong bullish setup detected for {symbol}:

        TECHNICAL ANALYSIS:
        - Multiple support levels identified at {[str(level.price) for level in technical_analysis.support_levels[:3]]}
        - Resistance targets at {[str(level.price) for level in technical_analysis.resistance_levels[:3]]}
        - Trend direction: {technical_analysis.trend_direction} with strength {technical_analysis.trend_strength}

        ENTRY STRATEGY:
        - Entry at current price ${current_price} near support confluence
        - Stop loss below key support at ${stop_loss}
        - Take profit at resistance level ${take_profit}

        RISK MANAGEMENT:
        - Risk-reward ratio: {risk_reward_ratio}:1
        - Position size: 3% of portfolio
        - Maximum risk: ${risk * 100} per share

        KEY FACTORS SUPPORTING THE TRADE:
        - Strong support level with {technical_analysis.support_levels[0].touches if technical_analysis.support_levels else 0} historical touches
        - Clear resistance target with favorable risk-reward
        - Technical momentum in bullish direction
        """,
        key_factors=[
            "Strong support levels detected",
            "Favorable risk-reward ratio",
            "Bullish technical momentum",
            "Clear resistance targets"
        ],
        potential_catalysts=[
            "Technical breakout above resistance",
            "Volume confirmation on breakout",
            "Sector rotation into growth"
        ],
        risks=[
            "Market-wide correction could break support",
            "Lower than expected volume",
            "Fundamental headwinds"
        ],
        created_at=datetime.now()
    )


async def main():
    """Main demonstration function."""
    # Setup logging
    setup_logging()
    logger.info("Starting Nix Trader AI Simple Demo")

    # Create sample instruments
    sample_instruments = [
        TradingInstrument(
            symbol="AAPL",
            name="Apple Inc.",
            instrument_type=InstrumentType.STOCK,
            exchange="NASDAQ",
            currency="USD",
            sector="Technology",
            is_favorite=True
        ),
        TradingInstrument(
            symbol="GOOGL",
            name="Alphabet Inc.",
            instrument_type=InstrumentType.STOCK,
            exchange="NASDAQ",
            currency="USD",
            sector="Technology",
            is_favorite=True
        )
    ]

    logger.info(f"Analyzing {len(sample_instruments)} sample instruments")

    recommendations = []

    for instrument in sample_instruments:
        logger.info(f"Processing {instrument.symbol}...")

        # Create sample price data
        price_data = create_sample_price_data(instrument.symbol)

        # Perform technical analysis with S/R detection
        technical_analysis = create_sample_technical_analysis(instrument.symbol, price_data)

        # Create trade recommendation
        recommendation = create_sample_trade_recommendation(instrument.symbol, technical_analysis)

        recommendations.append(recommendation)

        logger.info(f"✅ Generated recommendation for {instrument.symbol}")

    # Display results
    logger.info(f"\n{'='*60}")
    logger.info(f"TRADE RECOMMENDATIONS SUMMARY")
    logger.info(f"{'='*60}")

    for i, rec in enumerate(recommendations, 1):
        logger.info(f"\n{i}. {rec.symbol} - {rec.direction.upper()} {rec.timeframe.upper()} Trade")
        logger.info(f"   📈 Entry: ${rec.entry.price}")
        logger.info(f"   🛑 Stop Loss: ${rec.exit.stop_loss} ({rec.exit.stop_loss_percent:.1f}%)")
        logger.info(f"   🎯 Take Profit: ${rec.exit.take_profit[0]} ({rec.exit.take_profit_percents[0]:.1f}%)")
        logger.info(f"   ⚖️  Risk/Reward: {rec.risk.risk_reward_ratio:.2f}:1")
        logger.info(f"   📊 Overall Score: {rec.overall_score}/100")
        logger.info(f"   🎯 Confidence: {rec.confidence_level}%")

        # Display support/resistance levels
        if rec.technical_analysis and rec.technical_analysis.support_levels:
            support_prices = [str(level.price) for level in rec.technical_analysis.support_levels[:3]]
            logger.info(f"   📉 Key Support: {', '.join(support_prices)}")

        if rec.technical_analysis and rec.technical_analysis.resistance_levels:
            resistance_prices = [str(level.price) for level in rec.technical_analysis.resistance_levels[:3]]
            logger.info(f"   📈 Key Resistance: {', '.join(resistance_prices)}")

        logger.info(f"   💡 Key Factors: {', '.join(rec.key_factors[:2])}")

    logger.info(f"\n🎉 Analysis complete! Generated {len(recommendations)} actionable trade recommendations.")
    logger.info(f"💡 Each recommendation includes precise support/resistance levels for optimal entry/exit timing.")


if __name__ == "__main__":
    asyncio.run(main())