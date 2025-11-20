#!/usr/bin/env python3
"""Standalone script to run Gold Sentiment Analysis.

This script can be run directly without needing to use python -m
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from nix_trader_ai.agents.gold_sentiment_agent import run_gold_sentiment_analysis


async def main():
    """Run the Gold sentiment analysis."""
    print("🥇 Gold Sentiment Analysis Agent")
    print("=" * 60)
    print()

    try:
        result = await run_gold_sentiment_analysis()

        print()
        print("=" * 60)
        print("✅ Analysis Complete!")
        print("=" * 60)
        print()
        print(f"📊 Results:")
        print(f"   Symbol: {result.symbol}")
        print(f"   Overall Sentiment: {result.overall_sentiment:.2f}")
        print(f"   News Sentiment: {result.news_sentiment:.2f}")
        print(f"   Signal: {result.signal}")
        print(f"   Score: {result.score:.1f}/100")
        print(f"   Sources Analyzed: {result.sentiment_sources}")

        if result.key_themes:
            print()
            print(f"🎯 Key Themes:")
            for theme in result.key_themes[:5]:
                print(f"   • {theme}")

        print()
        print(f"⏰ Analyzed at: {result.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        return 1

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
