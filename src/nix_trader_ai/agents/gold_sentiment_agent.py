"""Specialized Gold sentiment analysis agent with news collection and Slack notifications."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import asyncio
import sys
from pathlib import Path

# Handle both direct execution and module imports
if __name__ == "__main__" and __package__ is None:
    # Running as script - add parent to path
    file_path = Path(__file__).resolve()
    parent_dir = file_path.parent.parent.parent
    sys.path.insert(0, str(parent_dir))
    __package__ = "nix_trader_ai.agents"

# Now do the imports
from ..utils.telemetry import configure_from_settings
from ..core.base_agent import BaseAgent
from ..models.analysis import SentimentAnalysis
from ..services.news_service import NewsService
from ..services.slack_service import SlackService
from ..services.yfinance_service import YFinanceService

# Ensure Logfire is configured
configure_from_settings()


class GoldSentimentAgent(BaseAgent[SentimentAnalysis]):
    """Specialized agent for Gold market sentiment analysis with notifications."""

    def __init__(
        self,
        news_service: Optional[NewsService] = None,
        slack_service: Optional[SlackService] = None,
        market_data_service: Optional[YFinanceService] = None,
        lookback_hours: int = 24
    ):
        """Initialize the Gold sentiment agent.

        Args:
            news_service: Service for fetching news articles
            slack_service: Service for sending Slack notifications
            market_data_service: Service for fetching market data and prices
            lookback_hours: Hours to look back for news articles
        """
        super().__init__(
            name="GoldSentiment",
            description="Specialized sentiment analysis for Gold markets with news collection and notifications"
        )
        self.news_service = news_service or NewsService()
        self.slack_service = slack_service
        self.market_data_service = market_data_service or YFinanceService()
        self.lookback_hours = lookback_hours
    def get_result_type(self) -> type[SentimentAnalysis]:
        """Return the result type."""
        return SentimentAnalysis

    def get_system_prompt(self) -> str:
        """Return the system prompt for Gold-specific sentiment analysis."""
        return """You are an expert Gold market sentiment analyst. Your role is to:

1. Analyze news articles and headlines specifically impacting Gold prices
2. Evaluate geopolitical events and their effect on Gold demand
3. Assess central bank policies and monetary decisions
4. Monitor inflation trends and currency movements
5. Track safe-haven demand and risk sentiment
6. Analyze mining sector news and supply dynamics
7. Evaluate jewelry demand and industrial usage trends

Key Gold-specific factors to analyze:
- Federal Reserve policy and interest rate expectations
- Dollar strength/weakness (inverse correlation with Gold)
- Geopolitical tensions and safe-haven flows
- Inflation expectations and real yields
- Central bank Gold purchases
- Mining production and supply disruptions
- Jewelry demand from major markets (India, China)
- ETF flows and institutional positioning
- Technical support/resistance levels
- Correlation with other precious metals

Provide sentiment scores (-1 to 1), price movement predictions (bullish/bearish/neutral),
confidence levels, and actionable insights for Gold traders."""

    async def analyze(self, context: Dict[str, Any]) -> SentimentAnalysis:
        """Perform comprehensive Gold sentiment analysis."""
        import logfire

        with logfire.span("gold_sentiment_analysis",
                         current_price=context.get("current_price"),
                         analysis_type="gold_sentiment"):
            # Fetch current market data for Gold
            with logfire.span("fetch_gold_market_data"):
                market_data = await self._fetch_gold_market_data()
                logfire.info(
                    "Fetched Gold market data",
                    current_price=market_data.get("current_price"),
                    price_change=market_data.get("change_percent")
                )

            # Collect latest Gold-related news
            with logfire.span("collect_gold_news"):
                news_items = await self._collect_gold_news()
                logfire.info(f"Collected {len(news_items)} news articles for Gold analysis")

            # Add market data and news to context
            context.update(market_data)
            context["news_items"] = news_items
            context["symbol"] = "XAU/USD"
            context["asset_class"] = "precious_metals"

            prompt = self._build_analysis_prompt(news_items, context)

            # Run the analysis
            with logfire.span("run_sentiment_ai_analysis",
                             article_count=len(news_items)):
                result = await self._run_agent(prompt, context)
                logfire.info(
                    "Gold sentiment analysis complete",
                    sentiment_score=result.overall_sentiment,
                    signal=result.signal,
                    confidence=result.score
                )

            # Send Slack notification if configured
            if self.slack_service:
                with logfire.span("send_slack_notification"):
                    await self._send_slack_notification(result, news_items, market_data)

            return result

    async def _fetch_gold_market_data(self) -> Dict[str, Any]:
        """Fetch current Gold market data and recent price history.

        Returns:
            Dictionary with current price, change, historical data, and trends
        """
        # Gold ticker symbol for Yahoo Finance
        symbol = "GC=F"  # Gold futures

        try:
            # Get current quote
            quote = await self.market_data_service.get_stock_quote(symbol)

            # Get recent price history (last 24 hours on hourly timeframe)
            price_history = await self.market_data_service.get_hourly_prices(symbol, hours=24)

            # Calculate trend indicators
            trend_info = self._calculate_trend_indicators(price_history, timeframe="24h")

            return {
                "current_price": quote.get("price", "N/A"),
                "price_change": quote.get("change", "N/A"),
                "change_percent": quote.get("change_percent", "N/A"),
                "volume": quote.get("volume", "N/A"),
                "latest_trading_day": quote.get("latest_trading_day", "N/A"),
                "recent_high_24h": trend_info.get("recent_high", "N/A"),
                "recent_low_24h": trend_info.get("recent_low", "N/A"),
                "price_trend_24h": trend_info.get("trend", "neutral"),
                "volatility_24h": trend_info.get("volatility", "N/A"),
                "price_momentum": trend_info.get("momentum", "N/A"),
            }
        except Exception as e:
            import logfire
            logfire.error(f"Error fetching Gold market data: {e}")
            return {
                "current_price": "N/A",
                "price_change": "N/A",
                "change_percent": "N/A",
                "error": str(e)
            }

    def _calculate_trend_indicators(self, price_history: List, timeframe: str = "24h") -> Dict[str, Any]:
        """Calculate trend indicators from price history.

        Args:
            price_history: List of PriceData objects
            timeframe: Timeframe string for display (e.g., "24h", "5d")

        Returns:
            Dictionary with trend indicators
        """
        if not price_history or len(price_history) < 2:
            return {
                "recent_high": "N/A",
                "recent_low": "N/A",
                "trend": "neutral",
                "volatility": "N/A",
                "momentum": "N/A"
            }

        # Extract close prices and high/low
        close_prices = [float(p.close_price) for p in price_history]
        high_prices = [float(p.high_price) for p in price_history]
        low_prices = [float(p.low_price) for p in price_history]

        # Calculate high and low for the period
        recent_high = max(high_prices)
        recent_low = min(low_prices)

        # Calculate trend (compare first and last)
        first_price = close_prices[-1]  # Oldest (list is reversed)
        last_price = close_prices[0]    # Most recent

        price_change_pct = ((last_price - first_price) / first_price) * 100

        # Determine trend based on hourly data (tighter thresholds for 24h)
        if timeframe == "24h":
            if price_change_pct > 0.5:  # Up more than 0.5% in 24h
                trend = "bullish"
            elif price_change_pct < -0.5:  # Down more than 0.5% in 24h
                trend = "bearish"
            else:
                trend = "neutral"
        else:
            # Daily data uses larger thresholds
            if price_change_pct > 1.0:
                trend = "bullish"
            elif price_change_pct < -1.0:
                trend = "bearish"
            else:
                trend = "neutral"

        # Calculate momentum (recent 6 hours vs previous 6 hours)
        momentum = "N/A"
        if len(close_prices) >= 12:  # Need at least 12 hours
            recent_6h_avg = sum(close_prices[0:6]) / 6
            previous_6h_avg = sum(close_prices[6:12]) / 6
            momentum_change = ((recent_6h_avg - previous_6h_avg) / previous_6h_avg) * 100

            if momentum_change > 0.3:
                momentum = "accelerating up"
            elif momentum_change < -0.3:
                momentum = "accelerating down"
            else:
                momentum = "steady"

        # Calculate simple volatility (standard deviation)
        if len(close_prices) > 1:
            mean_price = sum(close_prices) / len(close_prices)
            variance = sum((p - mean_price) ** 2 for p in close_prices) / len(close_prices)
            volatility = (variance ** 0.5) / mean_price * 100  # As percentage
            volatility_str = f"{volatility:.2f}%"
        else:
            volatility_str = "N/A"

        return {
            "recent_high": f"${recent_high:,.2f}",
            "recent_low": f"${recent_low:,.2f}",
            "trend": trend,
            "volatility": volatility_str,
            "momentum": momentum,
            "price_change_pct": f"{price_change_pct:+.2f}%"
        }

    async def _collect_gold_news(self) -> List[Dict[str, Any]]:
        """Collect latest news related to Gold markets.

        Returns:
            List of news articles with title, content, source, and timestamp
        """
        keywords = [
            "gold price",
            "XAU",
            "precious metals",
            "Federal Reserve gold",
            "central bank gold",
            "gold mining",
            "inflation gold",
            "safe haven gold"
        ]

        news_items = await self.news_service.fetch_news(
            keywords=keywords,
            lookback_hours=self.lookback_hours,
            max_articles=50
        )

        return news_items

    def _build_analysis_prompt(
        self,
        news_items: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Build the analysis prompt with collected news and market data."""
        current_price = context.get("current_price", "N/A")
        price_change = context.get("change_percent", "N/A")
        price_trend_24h = context.get("price_trend_24h", "neutral")
        recent_high_24h = context.get("recent_high_24h", "N/A")
        recent_low_24h = context.get("recent_low_24h", "N/A")
        volatility_24h = context.get("volatility_24h", "N/A")
        momentum = context.get("price_momentum", "N/A")

        news_summary = "\n\n".join([
            f"**{item.get('title', 'No title')}**\n"
            f"Source: {item.get('source', 'Unknown')} | "
            f"Time: {item.get('published_at', 'N/A')}\n"
            f"Summary: {item.get('content', item.get('description', ''))[:300]}..."
            for item in news_items[:20]
        ])

        prompt = f"""
        Perform comprehensive Gold (XAU/USD) sentiment analysis:

        ## Current Market Data (Hourly Timeframe - Last 24 Hours)
        Current Gold Price: {current_price}
        Price Change (Daily): {price_change}
        24h Trend: {price_trend_24h}
        24h High: {recent_high_24h}
        24h Low: {recent_low_24h}
        24h Volatility: {volatility_24h}
        Price Momentum: {momentum}
        Analysis Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

        ## Recent News and Reports ({len(news_items)} articles analyzed):
        {news_summary}

        ## Additional Market Context:
        {context.get('additional_context', 'N/A')}

        Analyze the following:

        1. **Overall Sentiment Score** (-1 to 1):
           - Aggregate sentiment from all news sources
           - Weight by source credibility and recency

        2. **Key Drivers**:
           - Identify top 3-5 factors currently impacting Gold
           - Rate their bullish/bearish impact (strong/moderate/weak)

        3. **Geopolitical & Macro Factors**:
           - Fed policy expectations and rate decisions
           - Dollar strength and currency movements
           - Geopolitical tensions and safe-haven demand
           - Inflation trends and real yield movements

        4. **Technical & Flow Analysis**:
           - Institutional positioning and ETF flows
           - Mining sector developments
           - Jewelry demand trends
           - Supply/demand imbalances

        5. **Price Movement Prediction**:
           - Short-term outlook (24-48 hours): Bullish/Neutral/Bearish
           - Medium-term outlook (1-2 weeks): Bullish/Neutral/Bearish
           - Confidence level (0-100%)
           - Key price levels to watch

        6. **Risk Factors**:
           - Events that could reverse current sentiment
           - Upcoming catalysts (data releases, Fed speeches, etc.)

        Provide actionable insights for traders and risk managers.
        """

        return prompt

    async def _send_slack_notification(
        self,
        analysis: SentimentAnalysis,
        news_items: List[Dict[str, Any]],
        market_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send formatted analysis to Slack.

        Args:
            analysis: The sentiment analysis result
            news_items: List of analyzed news articles
            market_data: Current market data (price, trend, etc.)
        """
        if not self.slack_service:
            return

        # Determine emoji based on sentiment
        sentiment_emoji = "🟡"  # Neutral
        if analysis.overall_sentiment > 0.3:
            sentiment_emoji = "🟢"  # Bullish
        elif analysis.overall_sentiment < -0.3:
            sentiment_emoji = "🔴"  # Bearish

        # Determine price prediction emoji
        price_emoji = "📊"
        if hasattr(analysis, 'price_prediction'):
            if analysis.price_prediction == 'bullish':
                price_emoji = "📈"
            elif analysis.price_prediction == 'bearish':
                price_emoji = "📉"

        # Build market data section
        market_fields = []
        if market_data:
            market_fields = [
                {
                    "type": "mrkdwn",
                    "text": f"*Current Price:*\n${market_data.get('current_price', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*24h Change:*\n{market_data.get('change_percent', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*24h High/Low:*\n{market_data.get('recent_high_24h', 'N/A')} / {market_data.get('recent_low_24h', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*24h Trend:*\n{market_data.get('price_trend_24h', 'N/A').title()}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Volatility:*\n{market_data.get('volatility_24h', 'N/A')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Momentum:*\n{market_data.get('price_momentum', 'N/A').title()}"
                }
            ]

        # Build message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{sentiment_emoji} Gold Market Sentiment Report"
                }
            }
        ]

        # Add market data section if available
        if market_fields:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📊 Market Data*"
                },
                "fields": market_fields
            })
            blocks.append({"type": "divider"})

        # Add sentiment analysis section
        blocks.extend([
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Sentiment Score:*\n{analysis.overall_sentiment:.2f} ({self._sentiment_label(analysis.overall_sentiment)})"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Confidence:*\n{getattr(analysis, 'confidence', 0):.0%}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Articles Analyzed:*\n{len(news_items)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Price Outlook:*\n{price_emoji} {getattr(analysis, 'price_prediction', 'N/A').title()}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Key Themes:*\n{self._format_themes(analysis.key_themes)}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{analysis.reasoning[:500]}..."
                }
            }
        ])

        message = {
            "text": f"{sentiment_emoji} Gold Sentiment Analysis - {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "blocks": blocks
        }

        # Add risk factors if present
        if hasattr(analysis, 'risk_factors') and analysis.risk_factors:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*⚠️ Risk Factors:*\n{self._format_list(analysis.risk_factors)}"
                }
            })

        await self.slack_service.send_message(message)

    def _sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label."""
        if score > 0.6:
            return "Very Bullish"
        elif score > 0.3:
            return "Bullish"
        elif score > -0.3:
            return "Neutral"
        elif score > -0.6:
            return "Bearish"
        else:
            return "Very Bearish"

    def _format_themes(self, themes: List[str]) -> str:
        """Format themes as bullet points."""
        if not themes:
            return "No specific themes identified"
        return "\n".join([f"• {theme}" for theme in themes[:5]])

    def _format_list(self, items: List[str]) -> str:
        """Format list items as bullet points."""
        if not items:
            return "None identified"
        return "\n".join([f"• {item}" for item in items[:5]])


async def run_gold_sentiment_analysis() -> SentimentAnalysis:
    """Main function to run Gold sentiment analysis.

    This is the entry point for cloud deployment (Lambda, Cloud Functions, etc.)

    Returns:
        SentimentAnalysis result
    """
    # Initialize services
    news_service = NewsService()
    slack_service = SlackService()
    market_data_service = YFinanceService()

    agent = GoldSentimentAgent(
        news_service=news_service,
        slack_service=slack_service,
        market_data_service=market_data_service
    )

    context = {
        "additional_context": "Automated periodic analysis"
    }

    result = await agent.analyze(context)
    return result


if __name__ == "__main__":
    # For local testing
    print("🥇 Running Gold Sentiment Analysis...\n")
    result = asyncio.run(run_gold_sentiment_analysis())
    print(f"\n✅ Analysis complete!")
    print(f"   Sentiment: {result.overall_sentiment:.2f}")
    print(f"   Signal: {result.signal}")
    print(f"   Score: {result.score:.1f}/100")
