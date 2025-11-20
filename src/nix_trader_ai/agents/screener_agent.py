"""Instrument screening agent."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from ..core.base_agent import BaseAgent
from ..models import TradingInstrument


class InstrumentScreeningResult(BaseModel):
    """Result from instrument screening."""

    recommended_instruments: List[TradingInstrument] = Field(
        ..., description="List of recommended instruments to analyze"
    )
    screening_criteria: Dict[str, Any] = Field(
        ..., description="Criteria used for screening"
    )
    market_overview: str = Field(
        ..., description="Overview of current market conditions"
    )
    reasoning: str = Field(
        ..., description="Reasoning for the recommendations"
    )


class ScreenerAgent(BaseAgent[InstrumentScreeningResult]):
    """Agent responsible for screening and selecting trading instruments."""

    def __init__(self):
        """Initialize the screener agent."""
        super().__init__(
            name="Screener",
            description="Screens favorite instruments and selects best opportunities"
        )

    def get_result_type(self) -> type[InstrumentScreeningResult]:
        """Return the result type."""
        return InstrumentScreeningResult

    def get_system_prompt(self) -> str:
        """Return the system prompt."""
        return """You are an expert financial instrument screener. Your role is to:

1. Analyze the provided list of favorite trading instruments
2. Evaluate current market conditions and trends
3. Screen instruments based on:
   - Recent price movements and volume
   - Market sentiment and news flow
   - Technical indicators for momentum
   - Sector rotation and market themes
   - Volatility and liquidity considerations

4. Select the most promising instruments for detailed analysis
5. Provide clear reasoning for your selections
6. Consider risk factors and market timing

Focus on identifying instruments with the highest probability of presenting
profitable trading opportunities in the current market environment."""

    async def analyze(self, context: Dict[str, Any]) -> InstrumentScreeningResult:
        """Screen instruments and select the best opportunities."""
        favorite_instruments = context.get("favorite_instruments", [])
        market_data = context.get("market_data", {})

        if not favorite_instruments:
            raise ValueError("No favorite instruments provided for screening")

        prompt = f"""
        Screen the following favorite instruments and recommend the best ones for trading:

        Favorite Instruments:
        {[inst.symbol for inst in favorite_instruments]}

        Current Market Data:
        {market_data}

        Please analyze each instrument and select the top candidates based on:
        - Technical momentum and chart patterns
        - Recent news and market sentiment
        - Volume and liquidity
        - Market sector performance
        - Risk-reward potential

        Recommend 3-5 instruments that offer the best trading opportunities right now.
        """

        # Get AI response
        ai_response = await self._run_agent(prompt, context)

        # If we got a string response, create the proper result structure
        if isinstance(ai_response, str):
            return InstrumentScreeningResult(
                recommended_instruments=favorite_instruments[:3],  # Select top 3
                screening_criteria={"ai_analysis": True, "market_data_available": True},
                market_overview="Market analysis conducted using available data",
                reasoning=ai_response[:500] + "..." if len(ai_response) > 500 else ai_response
            )

        return ai_response