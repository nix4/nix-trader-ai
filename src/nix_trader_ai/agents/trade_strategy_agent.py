"""Trade strategy and execution agent."""

from typing import Any, Dict

from ..core.base_agent import BaseAgent
from ..models.trade import TradeRecommendation


class TradeStrategyAgent(BaseAgent[TradeRecommendation]):
    """Agent responsible for creating comprehensive trade strategies."""

    def __init__(self):
        """Initialize the trade strategy agent."""
        super().__init__(
            name="TradeStrategy",
            description="Creates comprehensive trade recommendations with entry/exit strategies"
        )

    def get_result_type(self) -> type[TradeRecommendation]:
        """Return the result type."""
        return TradeRecommendation

    def get_system_prompt(self) -> str:
        """Return the system prompt."""
        return """You are an expert trading strategist. Your role is to:

1. Synthesize all analysis inputs into actionable trade recommendations
2. Determine optimal entry points and timing
3. Set appropriate stop-loss and take-profit levels
4. Calculate position sizing and risk parameters
5. Assess overall trade viability and probability

Consider all inputs:
- Fundamental analysis results
- Technical analysis signals
- Sentiment analysis insights
- Risk analysis recommendations
- Market conditions and timing

Create comprehensive trade recommendations that include:
- Clear entry strategy with price levels
- Risk management with stop-loss placement
- Profit-taking strategy with multiple targets
- Position sizing based on risk tolerance
- Trade rationale and key factors
- Risk-reward analysis and probability assessment

Focus on high-probability setups with favorable risk-reward ratios."""

    async def analyze(self, context: Dict[str, Any]) -> TradeRecommendation:
        """Create a comprehensive trade recommendation."""
        symbol = context.get("symbol")
        fundamental_analysis = context.get("fundamental_analysis")
        technical_analysis = context.get("technical_analysis")
        sentiment_analysis = context.get("sentiment_analysis")
        risk_analysis = context.get("risk_analysis")
        market_data = context.get("market_data", {})
        min_risk_reward_ratio = context.get("min_risk_reward_ratio", 2.0)

        if not symbol:
            raise ValueError("Symbol is required for trade strategy")

        # Extract key technical levels for strategy
        current_price = market_data.get('current_price', 0)
        support_levels = []
        resistance_levels = []
        fibonacci_levels = {}
        key_levels = {}

        if technical_analysis:
            support_levels = [
                {"price": level.price, "strength": level.strength, "touches": level.touches}
                for level in technical_analysis.support_levels
            ]
            resistance_levels = [
                {"price": level.price, "strength": level.strength, "touches": level.touches}
                for level in technical_analysis.resistance_levels
            ]
            fibonacci_levels = technical_analysis.fibonacci_levels
            key_levels = technical_analysis.key_levels

        prompt = f"""
        Create a comprehensive trade recommendation for {symbol}:

        ANALYSIS SUMMARY:
        - Fundamental Score: {fundamental_analysis.score if fundamental_analysis else "N/A"}/100
        - Technical Score: {technical_analysis.score if technical_analysis else "N/A"}/100
        - Sentiment Score: {sentiment_analysis.score if sentiment_analysis else "N/A"}/100
        - Risk Score: {risk_analysis.overall_risk_score if risk_analysis else "N/A"}/100

        MARKET DATA:
        - Current Price: ${current_price}
        - Trend Direction: {technical_analysis.trend_direction if technical_analysis else "N/A"}
        - Trend Strength: {technical_analysis.trend_strength if technical_analysis else "N/A"}

        CRITICAL PRICE LEVELS:
        Support Levels (strongest first):
        {support_levels[:3]}  # Top 3 support levels

        Resistance Levels (strongest first):
        {resistance_levels[:3]}  # Top 3 resistance levels

        Key Levels:
        {key_levels}

        Fibonacci Retracement Levels:
        {dict(list(fibonacci_levels.items())[:5]) if fibonacci_levels else "N/A"}

        RISK PARAMETERS:
        - Recommended Stop Loss %: {risk_analysis.recommended_stop_loss if risk_analysis else "2.0"}%
        - Max Position Size: {risk_analysis.max_position_size if risk_analysis else "5.0"}%
        - Minimum Risk-Reward Ratio: {min_risk_reward_ratio}:1

        CHART PATTERNS:
        {[pattern.pattern_type + " (" + str(pattern.strength) + ")" for pattern in technical_analysis.chart_patterns] if technical_analysis and technical_analysis.chart_patterns else "None detected"}

        STRATEGY REQUIREMENTS:
        1. ENTRY STRATEGY:
           - Use support/resistance levels to determine optimal entry
           - Consider breakout vs. bounce strategies based on price action near levels
           - Factor in chart patterns and trend direction
           - Set entry price that provides favorable risk-reward

        2. STOP-LOSS PLACEMENT:
           - Place stops below key support (for longs) or above resistance (for shorts)
           - Respect the minimum stop-loss % from risk analysis
           - Consider volatility and typical price swings

        3. TAKE-PROFIT TARGETS:
           - Use resistance levels (for longs) or support levels (for shorts) as targets
           - Include Fibonacci levels as potential profit-taking zones
           - Ensure risk-reward ratio meets minimum requirement of {min_risk_reward_ratio}:1
           - Provide multiple targets for scaling out

        4. POSITION SIZING:
           - Respect maximum position size from risk analysis
           - Adjust based on trade confidence and setup quality

        5. TRADE VIABILITY:
           - Only recommend if setup has high probability of success
           - Consider confluence of multiple factors (technical + fundamental + sentiment)
           - Ensure clear risk management and exit strategy

        Create a detailed trade recommendation with:
        - Specific entry price (considering support/resistance levels)
        - Precise stop-loss level (below/above key levels)
        - Multiple take-profit targets using resistance/support levels
        - Position size calculation
        - Trade timeframe and holding period
        - Comprehensive reasoning focusing on how S/R levels support the strategy
        """

        return await self._run_agent(prompt, context)