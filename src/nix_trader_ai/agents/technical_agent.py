"""Technical analysis agent."""

from typing import Any, Dict

from ..core.base_agent import BaseAgent
from ..models.analysis import TechnicalAnalysis, SupportResistanceLevel, ChartPattern
from ..models.market_data import PriceData
from ..utils.technical_indicators import TechnicalAnalyzer


class TechnicalAgent(BaseAgent[TechnicalAnalysis]):
    """Agent responsible for technical analysis of trading instruments."""

    def __init__(self):
        """Initialize the technical analysis agent."""
        super().__init__(
            name="Technical",
            description="Performs technical analysis on trading instruments"
        )

    def get_result_type(self) -> type[TechnicalAnalysis]:
        """Return the result type."""
        return TechnicalAnalysis

    def get_system_prompt(self) -> str:
        """Return the system prompt."""
        return """You are an expert technical analyst. Your role is to:

1. Analyze price charts and patterns
2. Calculate and interpret technical indicators:
   - Trend indicators (MA, EMA, MACD)
   - Momentum indicators (RSI, Stochastic)
   - Volume indicators (OBV, Volume MA)
   - Volatility indicators (Bollinger Bands, ATR)

3. Identify support and resistance levels
4. Recognize chart patterns (triangles, flags, head & shoulders, etc.)
5. Analyze trend direction and strength
6. Assess entry and exit points based on technical signals

Provide a comprehensive technical analysis with clear signals and actionable insights
for optimal entry/exit timing."""

    async def analyze(self, context: Dict[str, Any]) -> TechnicalAnalysis:
        """Perform technical analysis on the given instrument."""
        symbol = context.get("symbol")
        price_data_raw = context.get("price_data", [])
        volume_data = context.get("volume_data", [])
        indicators = context.get("indicators", {})

        if not symbol:
            raise ValueError("Symbol is required for technical analysis")

        # Convert raw price data to PriceData objects if needed
        price_data = []
        if price_data_raw:
            for item in price_data_raw:
                if isinstance(item, dict):
                    price_data.append(PriceData(**item))
                else:
                    price_data.append(item)

        # Perform technical analysis calculations
        analysis_results = await self._perform_technical_calculations(
            symbol, price_data, indicators
        )

        # Prepare enhanced context for AI agent
        enhanced_context = {
            **context,
            "calculated_support_levels": analysis_results["support_levels"],
            "calculated_resistance_levels": analysis_results["resistance_levels"],
            "fibonacci_levels": analysis_results["fibonacci_levels"],
            "chart_patterns": analysis_results["chart_patterns"],
            "trend_analysis": analysis_results["trend_analysis"]
        }

        prompt = f"""
        Perform comprehensive technical analysis for {symbol}:

        Price Data Summary:
        - Total periods: {len(price_data)}
        - Current price: {price_data[-1].close_price if price_data else "N/A"}
        - Price range (recent 20 periods): {min(p.low_price for p in price_data[-20:]) if len(price_data) >= 20 else "N/A"} - {max(p.high_price for p in price_data[-20:]) if len(price_data) >= 20 else "N/A"}

        Calculated Support Levels:
        {[{"price": level.price, "strength": level.strength, "touches": level.touches} for level in analysis_results["support_levels"]]}

        Calculated Resistance Levels:
        {[{"price": level.price, "strength": level.strength, "touches": level.touches} for level in analysis_results["resistance_levels"]]}

        Fibonacci Levels:
        {analysis_results["fibonacci_levels"]}

        Chart Patterns Detected:
        {analysis_results["chart_patterns"]}

        Technical Indicators:
        {indicators}

        Trend Analysis:
        {analysis_results["trend_analysis"]}

        Based on this comprehensive technical analysis:
        1. Evaluate the overall technical setup and momentum
        2. Assess the strength and reliability of support/resistance levels
        3. Analyze chart patterns and their implications
        4. Consider Fibonacci levels for potential reversal points
        5. Integrate indicator signals for timing
        6. Identify key levels for entry and exit strategies
        7. Determine trend direction and strength

        Provide a technical signal (strong_buy/buy/hold/sell/strong_sell) and score (0-100).
        Include detailed reasoning focusing on how support/resistance levels and patterns
        support your analysis and timing recommendations.
        """

        # Get AI analysis
        ai_result = await self._run_agent(prompt, enhanced_context)

        # Enhance the result with our calculated technical data
        ai_result.support_levels = analysis_results["support_levels"]
        ai_result.resistance_levels = analysis_results["resistance_levels"]
        ai_result.fibonacci_levels = analysis_results["fibonacci_levels"]
        ai_result.chart_patterns = analysis_results["chart_patterns"]
        ai_result.trend_strength = analysis_results["trend_analysis"].get("strength", 0.0)

        # Add key levels for easy reference
        ai_result.key_levels = {}
        if analysis_results["support_levels"]:
            ai_result.key_levels["nearest_support"] = analysis_results["support_levels"][0].price
        if analysis_results["resistance_levels"]:
            ai_result.key_levels["nearest_resistance"] = analysis_results["resistance_levels"][0].price

        return ai_result

    async def _perform_technical_calculations(
        self, symbol: str, price_data: list, indicators: dict
    ) -> Dict[str, Any]:
        """Perform technical calculations including support/resistance detection."""
        results = {
            "support_levels": [],
            "resistance_levels": [],
            "fibonacci_levels": {},
            "chart_patterns": [],
            "trend_analysis": {}
        }

        if not price_data or len(price_data) < 20:
            return results

        try:
            # Find support and resistance levels
            sr_levels = TechnicalAnalyzer.find_support_resistance_levels(
                price_data=price_data,
                lookback_period=10,
                min_touches=2,
                price_tolerance_percent=0.75
            )

            # Convert to Pydantic models
            results["support_levels"] = [
                SupportResistanceLevel(
                    price=level.price,
                    level_type=level.level_type,
                    strength=level.strength,
                    touches=level.touches
                ) for level in sr_levels["support"]
            ]

            results["resistance_levels"] = [
                SupportResistanceLevel(
                    price=level.price,
                    level_type=level.level_type,
                    strength=level.strength,
                    touches=level.touches
                ) for level in sr_levels["resistance"]
            ]

            # Calculate Fibonacci levels
            results["fibonacci_levels"] = TechnicalAnalyzer.calculate_fibonacci_levels(price_data)

            # Identify chart patterns
            pattern_data = TechnicalAnalyzer.identify_chart_patterns(price_data)
            results["chart_patterns"] = [
                ChartPattern(
                    pattern_type=pattern["type"],
                    strength=pattern["strength"],
                    description=pattern["description"],
                    timeframe="daily"  # Could be parameterized
                ) for pattern in pattern_data
            ]

            # Trend analysis
            if pattern_data:
                main_pattern = pattern_data[0]  # Primary pattern
                results["trend_analysis"] = {
                    "direction": main_pattern["type"],
                    "strength": main_pattern["strength"],
                    "description": main_pattern["description"]
                }

        except Exception as e:
            self.logger.error(f"Error in technical calculations for {symbol}: {str(e)}")

        return results