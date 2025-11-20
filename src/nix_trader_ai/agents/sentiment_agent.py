"""Sentiment analysis agent."""

from typing import Any, Dict

from ..core.base_agent import BaseAgent
from ..models.analysis import SentimentAnalysis


class SentimentAgent(BaseAgent[SentimentAnalysis]):
    """Agent responsible for sentiment analysis of trading instruments."""

    def __init__(self):
        """Initialize the sentiment analysis agent."""
        super().__init__(
            name="Sentiment",
            description="Performs sentiment analysis on news and market data"
        )

    def get_result_type(self) -> type[SentimentAnalysis]:
        """Return the result type."""
        return SentimentAnalysis

    def get_system_prompt(self) -> str:
        """Return the system prompt."""
        return """You are an expert sentiment analyst. Your role is to:

1. Analyze news articles and headlines for sentiment
2. Process social media mentions and discussions
3. Evaluate analyst reports and recommendations
4. Assess market sentiment indicators
5. Identify sentiment shifts and trends
6. Consider sentiment contrarian indicators

Key areas to analyze:
- Overall market sentiment towards the instrument
- News sentiment (positive/negative/neutral)
- Social media buzz and retail sentiment
- Institutional sentiment and analyst opinions
- Sector-specific sentiment trends
- Sentiment momentum and changes

Provide sentiment scores (-1 to 1) and identify key themes driving sentiment."""

    async def analyze(self, context: Dict[str, Any]) -> SentimentAnalysis:
        """Perform sentiment analysis on the given instrument."""
        symbol = context.get("symbol")
        news_items = context.get("news_items", [])
        social_data = context.get("social_data", [])
        analyst_data = context.get("analyst_data", {})

        if not symbol:
            raise ValueError("Symbol is required for sentiment analysis")

        prompt = f"""
        Perform sentiment analysis for {symbol}:

        Recent News Items:
        {[{"title": item.title, "content": item.content[:200]} for item in news_items[-10:]]}

        Social Media Data:
        {social_data}

        Analyst Data:
        {analyst_data}

        Analyze the sentiment landscape for this instrument:
        - Process news headlines and content for sentiment
        - Evaluate the tone and implications of recent coverage
        - Assess social media sentiment and retail investor mood
        - Consider analyst sentiment and recommendation changes
        - Identify key themes and sentiment drivers
        - Look for sentiment momentum and potential reversals

        Provide overall sentiment score (-1 to 1), individual component scores,
        and key themes driving current sentiment.
        """

        return await self._run_agent(prompt, context)