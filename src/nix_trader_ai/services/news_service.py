"""News collection service for market sentiment analysis."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx
from loguru import logger


class NewsService:
    """Service for fetching news articles from various sources."""

    def __init__(
        self,
        alpha_vantage_key: Optional[str] = None,
        use_gdelt: bool = True
    ):
        """Initialize news service with API keys.

        Args:
            alpha_vantage_key: Alpha Vantage API key for news
            use_gdelt: Whether to use GDELT (default True, no API key needed)
        """
        # Import settings here to avoid circular imports
        from ..core.config import settings

        self.alpha_vantage_key = alpha_vantage_key or settings.alpha_vantage_api_key
        self.use_gdelt = use_gdelt

        # Try to import GDELT
        self.gdelt_available = False
        if use_gdelt:
            try:
                from gdeltdoc import GdeltDoc, Filters
                self.GdeltDoc = GdeltDoc
                self.Filters = Filters
                self.gdelt_available = True
                logger.info("GDELT DOC API initialized successfully")
            except ImportError:
                logger.warning(
                    "gdeltdoc package not installed. Install with: pip install gdeltdoc"
                )
                logger.info("Falling back to Alpha Vantage or mock data")

    async def fetch_news(
        self,
        keywords: List[str],
        lookback_hours: int = 72,
        max_articles: int = 50
    ) -> List[Dict[str, Any]]:
        """Fetch news articles matching keywords.

        Args:
            keywords: List of keywords to search for
            lookback_hours: How many hours back to search (GDELT supports up to 3 months)
            max_articles: Maximum number of articles to return

        Returns:
            List of news articles with title, content, source, and timestamp
        """
        all_articles = []

        # Try GDELT first (free, real-time, no API key needed)
        if self.gdelt_available:
            try:
                gdelt_articles = await self._fetch_from_gdelt(
                    keywords, lookback_hours, max_articles
                )
                all_articles.extend(gdelt_articles)
                logger.info(f"GDELT returned {len(gdelt_articles)} articles")
            except Exception as e:
                logger.error(f"Error fetching from GDELT: {e}")
                import traceback
                logger.error(traceback.format_exc())

        # Try Alpha Vantage if we need more articles
        if self.alpha_vantage_key and len(all_articles) < max_articles:
            try:
                av_articles = await self._fetch_from_alpha_vantage(
                    keywords, lookback_hours, max_articles - len(all_articles)
                )
                all_articles.extend(av_articles)
            except Exception as e:
                logger.error(f"Error fetching from Alpha Vantage: {e}")

        # If no articles found, use mock data for testing
        if not all_articles:
            logger.warning("No news articles fetched, using mock data for testing")
            all_articles = self._get_mock_news(keywords)

        # Sort by published date (newest first)
        all_articles.sort(
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )

        return all_articles[:max_articles]

    async def _fetch_from_gdelt(
        self,
        keywords: List[str],
        lookback_hours: int,
        max_articles: int
    ) -> List[Dict[str, Any]]:
        """Fetch articles from GDELT DOC API.

        GDELT provides real-time news from global sources with no API key required.
        Data freshness: Near real-time (15-minute updates)
        Coverage: 100+ languages, global sources
        Rate limits: None (free and open)

        Args:
            keywords: Search keywords
            lookback_hours: Hours to look back (max ~3 months)
            max_articles: Maximum articles to fetch

        Returns:
            List of formatted articles
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        # GDELT is synchronous, so we'll run it in a thread pool
        def fetch_sync():
            import pandas as pd

            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=lookback_hours)

            # Build search queries for GDELT
            # GDELT requires phrases to be at least 2 words, and has issues with OR operators
            # Strategy: Query multiple relevant phrases and combine results
            search_phrases = []

            if keywords:
                # Extract multi-word phrases (already valid for GDELT)
                multi_word = [kw for kw in keywords if len(kw.split()) >= 2]
                search_phrases.extend(multi_word[:3])  # Limit to top 3 multi-word phrases

            # If we don't have enough phrases, add "gold price" as default
            if not search_phrases:
                search_phrases = ["gold price"]

            # Initialize GDELT client
            gd = self.GdeltDoc()

            # Query multiple phrases and combine results
            all_dfs = []
            articles_per_phrase = max(max_articles // len(search_phrases), 30)

            for phrase in search_phrases[:3]:  # Limit to 3 queries to avoid excessive API calls
                try:
                    filters = self.Filters(
                        keyword=phrase,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        num_records=min(articles_per_phrase * 3, 100)  # Request extras for English filtering
                    )

                    logger.info(f"Querying GDELT for: '{phrase}' from {start_date} to {end_date}")
                    df = gd.article_search(filters)

                    if df is not None and not df.empty:
                        all_dfs.append(df)
                        logger.debug(f"Got {len(df)} articles for '{phrase}'")

                except Exception as e:
                    logger.warning(f"Error querying GDELT for '{phrase}': {e}")
                    continue

            # Combine all dataframes and remove duplicates
            if all_dfs:
                combined_df = pd.concat(all_dfs, ignore_index=True)
                # Remove duplicates based on URL
                combined_df = combined_df.drop_duplicates(subset=['url'], keep='first')
                logger.info(f"Combined {len(combined_df)} unique articles from {len(all_dfs)} queries")
                return combined_df
            else:
                logger.warning("No results from any GDELT query")
                return None

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            df = await loop.run_in_executor(executor, fetch_sync)

        # Convert DataFrame to list of dicts
        articles = []
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                # GDELT returns: url, title, domain, language, seendate
                language = str(row.get("language", "")).lower()

                # Filter for English articles - GDELT uses full language names like "English"
                # Also include articles with no language specified (often English)
                is_english = (
                    "english" in language or
                    language == "en" or
                    language == "" or
                    language == "none" or
                    language == "nan"
                )

                if is_english:
                    title = str(row.get("title", "No title"))

                    # Basic check: skip if title is mostly non-ASCII (likely non-English even if marked as English)
                    # But allow some special characters (quotes, accents, etc.)
                    non_ascii_ratio = sum(1 for char in title if ord(char) > 255) / max(len(title), 1)
                    if non_ascii_ratio > 0.3:  # More than 30% non-Latin characters
                        continue

                    articles.append({
                        "title": title,
                        "description": "",  # GDELT doesn't provide descriptions
                        "content": "",  # Would need to scrape the URL for full content
                        "source": row.get("domain", "Unknown"),
                        "url": row.get("url", ""),
                        "published_at": row.get("seendate", datetime.utcnow().isoformat()),
                        "language": language if language else "en",
                    })

                    # Stop if we have enough articles
                    if len(articles) >= max_articles:
                        break

            logger.info(f"Fetched {len(articles)} English articles from GDELT (filtered from {len(df)} total)")
        else:
            logger.warning("GDELT returned no results")

        return articles

    async def _fetch_from_alpha_vantage(
        self,
        keywords: List[str],
        lookback_hours: int,
        max_articles: int
    ) -> List[Dict[str, Any]]:
        """Fetch articles from Alpha Vantage News API.

        Args:
            keywords: Search keywords
            lookback_hours: Hours to look back
            max_articles: Maximum articles to fetch

        Returns:
            List of formatted articles
        """
        base_url = "https://www.alphavantage.co/query"

        # Alpha Vantage supports topics and tickers
        # For gold, we'll use relevant topics
        topics = "financial_markets,economy_fiscal,finance"

        from_time = (datetime.utcnow() - timedelta(hours=lookback_hours)).strftime(
            "%Y%m%dT%H%M"
        )

        params = {
            "function": "NEWS_SENTIMENT",
            "topics": topics,
            "time_from": from_time,
            "limit": min(max_articles, 1000),
            "apikey": self.alpha_vantage_key
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

        articles = []
        for item in data.get("feed", []):
            # Filter by keywords in title or summary
            title = item.get("title", "").lower()
            summary = item.get("summary", "").lower()

            if any(kw.lower() in title or kw.lower() in summary for kw in keywords):
                articles.append({
                    "title": item.get("title", ""),
                    "description": item.get("summary", ""),
                    "content": item.get("summary", ""),
                    "source": ", ".join([s.get("name", "") for s in item.get("authors", [])]) or "Alpha Vantage",
                    "url": item.get("url", ""),
                    "published_at": item.get("time_published", ""),
                    "sentiment_score": item.get("overall_sentiment_score", 0),
                    "sentiment_label": item.get("overall_sentiment_label", "Neutral"),
                })

        logger.info(f"Fetched {len(articles)} articles from Alpha Vantage")
        return articles

    def _get_mock_news(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Generate mock news data for testing when no API keys are available.

        Args:
            keywords: Keywords that were searched for

        Returns:
            List of mock articles
        """
        now = datetime.utcnow()

        mock_articles = [
            {
                "title": "Gold Prices Surge on Fed Rate Cut Expectations",
                "description": "Gold prices climbed to new highs as markets price in potential Federal Reserve rate cuts amid cooling inflation data.",
                "content": "Gold prices surged today as investors bet on Federal Reserve rate cuts in the coming months. The precious metal gained 2.3% to reach $2,050 per ounce, driven by dovish comments from Fed officials and weaker-than-expected inflation data. Lower interest rates typically benefit gold as they reduce the opportunity cost of holding non-yielding assets.",
                "source": "Financial Times",
                "url": "https://example.com/gold-fed-rates",
                "published_at": (now - timedelta(hours=2)).isoformat(),
                "author": "Market Analyst",
            },
            {
                "title": "Central Banks Continue Gold Buying Spree",
                "description": "Major central banks increased gold reserves for the fifth consecutive quarter, supporting prices.",
                "content": "Central banks around the world continue to accumulate gold reserves, with purchases totaling 450 tonnes in Q4. China, India, and Poland led the buying activity, reflecting concerns about currency diversification and geopolitical uncertainty. This sustained demand from official institutions provides a strong floor for gold prices.",
                "source": "Reuters",
                "url": "https://example.com/central-bank-gold",
                "published_at": (now - timedelta(hours=5)).isoformat(),
                "author": "Reuters Staff",
            },
            {
                "title": "Dollar Weakness Boosts Gold Appeal",
                "description": "The US dollar's decline to multi-month lows is making gold more attractive to international buyers.",
                "content": "The US dollar fell to its lowest level in three months against a basket of major currencies, providing additional support for gold prices. The inverse relationship between the dollar and gold was on full display as the precious metal gained nearly 3% this week. Currency traders point to expectations of Fed rate cuts as the main driver of dollar weakness.",
                "source": "Bloomberg",
                "url": "https://example.com/dollar-gold",
                "published_at": (now - timedelta(hours=8)).isoformat(),
                "author": "Currency Desk",
            },
            {
                "title": "Geopolitical Tensions Drive Safe-Haven Demand",
                "description": "Rising geopolitical uncertainty in the Middle East is boosting gold's safe-haven appeal.",
                "content": "Gold prices received a boost from escalating geopolitical tensions, with investors seeking the safety of the precious metal. The situation in the Middle East and ongoing trade disputes are creating an uncertain environment that traditionally benefits gold. ETF inflows have accelerated, with major gold ETFs seeing their largest weekly inflows in six months.",
                "source": "Wall Street Journal",
                "url": "https://example.com/geopolitics-gold",
                "published_at": (now - timedelta(hours=12)).isoformat(),
                "author": "Commodities Reporter",
            },
            {
                "title": "Mining Sector Faces Production Challenges",
                "description": "Major gold miners report production setbacks, potentially tightening supply.",
                "content": "Several major gold mining companies have revised down their production guidance for the year due to operational challenges and lower ore grades. Barrick Gold and Newmont both cited technical issues at key mines, while rising energy costs are squeezing margins across the sector. Analysts suggest these supply constraints could support higher gold prices in the medium term.",
                "source": "Mining Weekly",
                "url": "https://example.com/mining-production",
                "published_at": (now - timedelta(hours=18)).isoformat(),
                "author": "Mining Correspondent",
            }
        ]

        return mock_articles
