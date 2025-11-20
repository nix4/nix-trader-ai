"""Risk analysis agent."""

from typing import Any, Dict

from ..core.base_agent import BaseAgent
from ..models.analysis import RiskAnalysis


class RiskAgent(BaseAgent[RiskAnalysis]):
    """Agent responsible for risk analysis of trading instruments."""

    def __init__(self):
        """Initialize the risk analysis agent."""
        super().__init__(
            name="Risk",
            description="Performs comprehensive risk analysis for trading decisions"
        )

    def get_result_type(self) -> type[RiskAnalysis]:
        """Return the result type."""
        return RiskAnalysis

    def get_system_prompt(self) -> str:
        """Return the system prompt."""
        return """You are an expert risk analyst. Your role is to:

1. Assess various types of trading risks:
   - Market risk (systematic risk, beta)
   - Volatility risk (price swings, VaR)
   - Liquidity risk (bid-ask spreads, volume)
   - Fundamental risk (business, financial)
   - Event risk (earnings, announcements)

2. Calculate risk metrics and scores
3. Determine appropriate position sizing
4. Recommend stop-loss levels
5. Identify risk factors and mitigation strategies

Consider:
- Historical volatility and correlation
- Current market conditions and regime
- Instrument-specific risk factors
- Portfolio concentration and diversification
- Risk-adjusted return expectations

Provide comprehensive risk assessment with actionable risk management recommendations."""

    async def analyze(self, context: Dict[str, Any]) -> RiskAnalysis:
        """Perform risk analysis on the given instrument."""
        symbol = context.get("symbol")
        market_data = context.get("market_data", {})
        price_history = context.get("price_history", [])
        portfolio_data = context.get("portfolio_data", {})
        fundamental_analysis = context.get("fundamental_analysis")
        technical_analysis = context.get("technical_analysis")

        if not symbol:
            raise ValueError("Symbol is required for risk analysis")

        prompt = f"""
        Perform comprehensive risk analysis for {symbol}:

        Market Data:
        {market_data}

        Price History (for volatility calculation):
        {price_history[-100:] if price_history else "Limited price history"}

        Portfolio Context:
        {portfolio_data}

        Previous Analyses:
        Fundamental Score: {fundamental_analysis.score if fundamental_analysis else "N/A"}
        Technical Score: {technical_analysis.score if technical_analysis else "N/A"}

        Assess the following risk dimensions:
        - Volatility risk based on historical price movements
        - Liquidity risk from volume and market cap
        - Market risk from beta and correlation
        - Fundamental risk from business and financial metrics
        - Event risk from upcoming catalysts

        Calculate:
        - Overall risk score (0-100, higher = riskier)
        - Component risk scores
        - Maximum recommended position size
        - Suggested stop-loss percentage
        - Key risk factors to monitor

        Consider current market volatility and regime in your assessment.
        """

        return await self._run_agent(prompt, context)