#!/usr/bin/env python3
"""Test script for Gold Sentiment Agent."""

import asyncio
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from nix_trader_ai.agents.gold_sentiment_agent import GoldSentimentAgent
from nix_trader_ai.services.news_service import NewsService
from nix_trader_ai.services.slack_service import SlackService


async def test_news_collection():
    """Test news collection service."""
    print("=" * 60)
    print("Testing News Collection Service")
    print("=" * 60)

    news_service = NewsService()

    print("\n📰 Fetching Gold-related news...")
    news_items = await news_service.fetch_news(
        keywords=["gold price", "XAU", "precious metals"],
        lookback_hours=24,
        max_articles=10
    )

    print(f"\n✓ Found {len(news_items)} articles")

    # Display first 3 articles
    for i, article in enumerate(news_items[:3], 1):
        print(f"\n{i}. {article.get('title', 'No title')}")
        print(f"   Source: {article.get('source', 'Unknown')}")
        print(f"   Published: {article.get('published_at', 'N/A')}")
        print(f"   Summary: {article.get('content', '')[:150]}...")

    return news_items


async def test_slack_notification():
    """Test Slack notification service."""
    print("\n" + "=" * 60)
    print("Testing Slack Notification Service")
    print("=" * 60)

    slack_service = SlackService()

    # Create a test message
    test_message = {
        "text": "🧪 Test notification from Gold Sentiment Agent",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🧪 Test Gold Sentiment Report"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Sentiment Score:*\n0.75 (Bullish)"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Confidence:*\n85%"
                    }
                ]
            }
        ]
    }

    print("\n📱 Sending test notification to Slack...")
    result = await slack_service.send_message(test_message)

    if result:
        print("✓ Slack notification sent successfully!")
    else:
        print("⚠ Slack notification skipped (no credentials configured)")
        print("   Set SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN to enable notifications")

    return result


async def test_gold_sentiment_analysis():
    """Test Gold sentiment analysis agent."""
    print("\n" + "=" * 60)
    print("Testing Gold Sentiment Analysis Agent")
    print("=" * 60)

    # Initialize services
    news_service = NewsService()
    slack_service = SlackService()

    # Initialize the Gold sentiment agent
    print("\n🤖 Initializing Gold Sentiment Agent...")
    agent = GoldSentimentAgent(
        news_service=news_service,
        slack_service=slack_service
    )

    print("✓ Agent initialized")
    print(f"   Name: {agent.name}")
    print(f"   Description: {agent.description}")

    # Prepare context
    context = {
        "current_price": 2050.00,
        "additional_context": "Local test run"
    }

    # Run the analysis
    print("\n🔍 Running Gold sentiment analysis...")
    print("   (This may take 30-60 seconds...)")

    try:
        result = await agent.analyze(context)

        print("\n" + "=" * 60)
        print("✓ Analysis Complete!")
        print("=" * 60)

        print(f"\n📊 Results:")
        print(f"   Symbol: {result.symbol}")
        print(f"   Overall Sentiment: {result.overall_sentiment:.2f}")
        print(f"   News Sentiment: {result.news_sentiment:.2f}")
        print(f"   Signal: {result.signal}")
        print(f"   Score: {result.score:.1f}/100")
        print(f"   Sources Analyzed: {result.sentiment_sources}")

        if result.key_themes:
            print(f"\n🎯 Key Themes:")
            for theme in result.key_themes[:5]:
                print(f"   • {theme}")

        print(f"\n📝 Summary:")
        summary_preview = result.reasoning[:300]
        print(f"   {summary_preview}...")

        print(f"\n⏰ Analysis Time: {result.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}")

        return result

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("🥇 GOLD SENTIMENT AGENT - LOCAL TEST")
    print("=" * 60)

    try:
        # Test 1: News Collection
        news_items = await test_news_collection()

        # Test 2: Slack Notification
        await test_slack_notification()

        # Test 3: Full Analysis
        result = await test_gold_sentiment_analysis()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)

        if result:
            print("\n✓ Gold sentiment analysis successful!")
            print(f"✓ Analyzed {len(news_items)} news articles")
            print(f"✓ Generated sentiment score: {result.overall_sentiment:.2f}")
        else:
            print("\n⚠ Some tests may have failed - check output above")

    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
