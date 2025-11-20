"""Fundamental analysis agent."""

from typing import Any, Dict

import logfire

from ..core.base_agent import BaseAgent
from ..models.analysis import FundamentalAnalysis


class FundamentalAgent(BaseAgent[FundamentalAnalysis]):
    """Agent responsible for fundamental analysis of trading instruments."""

    def __init__(self):
        """Initialize the fundamental analysis agent."""
        super().__init__(
            name="Fundamental",
            description="Performs fundamental analysis on trading instruments"
        )

    def get_result_type(self) -> type[FundamentalAnalysis]:
        """Return the result type."""
        return FundamentalAnalysis

    def get_system_prompt(self) -> str:
        """Return the system prompt."""
        return """You are an expert fundamental analyst. Your role is to:

1. Analyze financial statements and key metrics
2. Evaluate company fundamentals including:
   - Valuation ratios (P/E, P/B, PEG)
   - Profitability metrics (ROE, ROA, margins)
   - Financial health (debt ratios, cash flow)
   - Growth metrics (revenue, earnings growth)
   - Dividend analysis

3. Compare metrics to industry peers and historical averages
4. Assess business model strength and competitive advantages
5. Evaluate management quality and corporate governance
6. Consider macroeconomic factors affecting the company/sector

Provide a comprehensive fundamental analysis with a clear signal (strong_buy, buy, hold, sell, strong_sell)
and detailed reasoning supporting your conclusion."""

    @logfire.instrument("fundamental_agent_analyze", extract_args=True)
    async def analyze(self, context: Dict[str, Any]) -> FundamentalAnalysis:
        """Perform fundamental analysis on the given instrument."""
        symbol = context.get("symbol")
        market_data = context.get("market_data", {})
        financial_data = context.get("financial_data", {})

        if not symbol:
            raise ValueError("Symbol is required for fundamental analysis")

        prompt = f"""
        Perform fundamental analysis for {symbol}:

        Market Data:
        {market_data}

        Financial Data:
        {financial_data}

        Analyze the fundamental health and valuation of this instrument.
        Consider:
        - Current valuation metrics and how they compare to peers
        - Financial strength and profitability trends
        - Growth prospects and business model sustainability
        - Risk factors and competitive position
        - Macroeconomic impact on the sector

        Provide a fundamental signal and score (0-100) with detailed reasoning.
        """

        return await self._run_agent(prompt, context)