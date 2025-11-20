"""Main orchestrator for the trading analysis pipeline."""

import asyncio
from typing import Dict, List, Optional

import logfire
from loguru import logger

from ..agents import (
    FundamentalAgent,
    RiskAgent,
    ScreenerAgent,
    SentimentAgent,
    TechnicalAgent,
    TradeStrategyAgent,
)
from ..models import TradingInstrument
from ..models.trade import TradeRecommendation
from ..services.market_data_service import MarketDataService
from .config import settings


class TradingOrchestrator:
    """Main orchestrator that coordinates all trading agents."""

    def __init__(self):
        """Initialize the trading orchestrator."""
        self.logger = logger.bind(component="orchestrator")

        # Initialize services
        self.market_data_service = MarketDataService()

        # Initialize agents
        self.screener_agent = ScreenerAgent()
        self.fundamental_agent = FundamentalAgent()
        self.technical_agent = TechnicalAgent()
        self.sentiment_agent = SentimentAgent()
        self.risk_agent = RiskAgent()
        self.trade_strategy_agent = TradeStrategyAgent()

        self.logger.info("Trading orchestrator initialized")

    @logfire.instrument("screen_instruments", extract_args=True)
    async def screen_instruments(
        self,
        favorite_instruments: List[TradingInstrument]
    ) -> Dict:
        """
        Screen favorite instruments to identify best trading opportunities.

        Args:
            favorite_instruments: List of user's favorite trading instruments

        Returns:
            Dictionary containing screening results and recommendations
        """
        try:
            self.logger.info(f"Screening {len(favorite_instruments)} favorite instruments")

            with logfire.span("screening_preparation"):
                logfire.info("Starting instrument screening", instruments_count=len(favorite_instruments))

            # Get market overview for screening
            market_overview = {}
            with logfire.span("market_data_collection"):
                for instrument in favorite_instruments:
                    try:
                        with logfire.span("get_market_data", symbol=instrument.symbol):
                            market_data = await self.market_data_service.get_market_data(instrument)
                            market_overview[instrument.symbol] = {
                                "current_price": market_data.current_price,
                                "volume": market_data.volume_24h,
                                "news_count": len(market_data.news_items),
                                "volatility": "medium",  # Could be calculated from price history
                                "momentum": "neutral"     # Could be derived from technical indicators
                            }
                    except Exception as e:
                        self.logger.warning(f"Error getting market data for {instrument.symbol}: {e}")
                        logfire.error("Market data collection failed", symbol=instrument.symbol, error=str(e))
                        continue

            # Run screener agent
            context = {
                "favorite_instruments": favorite_instruments,
                "market_data": market_overview
            }

            with logfire.span("screener_analysis"):
                screening_result = await self.screener_agent.analyze(context)

            return {
                "screening_result": screening_result,
                "market_overview": market_overview,
                "recommended_instruments": screening_result.recommended_instruments if hasattr(screening_result, 'recommended_instruments') else favorite_instruments[:3]
            }

        except Exception as e:
            self.logger.error(f"Error in instrument screening: {str(e)}")
            return {
                "screening_result": None,
                "market_overview": {},
                "recommended_instruments": favorite_instruments[:1]  # Fallback to first instrument
            }

    @logfire.instrument("analyze_selected_instruments", extract_args=True)
    async def analyze_selected_instruments(
        self,
        selected_instruments: List[TradingInstrument],
        portfolio_data: Optional[Dict] = None
    ) -> List[TradeRecommendation]:
        """
        Analyze specific selected instruments for trading opportunities.

        Args:
            selected_instruments: List of instruments selected for analysis
            portfolio_data: Optional portfolio context for risk management

        Returns:
            List of trade recommendations
        """
        try:
            self.logger.info(f"Starting detailed analysis for {len(selected_instruments)} selected instruments")

            with logfire.span("analysis_preparation"):
                logfire.info(
                    "Starting detailed instrument analysis",
                    instruments_count=len(selected_instruments),
                    instruments=[inst.symbol for inst in selected_instruments]
                )

            # Analyze each selected instrument
            trade_recommendations = []

            for instrument in selected_instruments:
                try:
                    with logfire.span("analyze_single_instrument", symbol=instrument.symbol):
                        self.logger.info(f"Analyzing {instrument.symbol}")
                        logfire.info("Starting single instrument analysis", symbol=instrument.symbol)

                        recommendation = await self._analyze_instrument(instrument, portfolio_data)
                        if recommendation:
                            trade_recommendations.append(recommendation)
                            logfire.info(
                                "Instrument analysis completed",
                                symbol=instrument.symbol,
                                score=recommendation.overall_score,
                                direction=recommendation.direction
                            )
                except Exception as e:
                    self.logger.error(f"Error analyzing {instrument.symbol}: {str(e)}")
                    logfire.error("Instrument analysis failed", symbol=instrument.symbol, error=str(e))
                    continue

            # Sort recommendations by overall score
            with logfire.span("sort_recommendations"):
                trade_recommendations.sort(key=lambda x: x.overall_score, reverse=True)

            self.logger.info(f"Generated {len(trade_recommendations)} trade recommendations")
            logfire.info("Analysis completed", recommendations_count=len(trade_recommendations))
            return trade_recommendations

        except Exception as e:
            self.logger.error(f"Error in trading analysis pipeline: {str(e)}")
            return []

    async def analyze_trading_opportunities(
        self,
        favorite_instruments: List[TradingInstrument],
        portfolio_data: Optional[Dict] = None,
        skip_screening: bool = False,
        selected_instruments: Optional[List[TradingInstrument]] = None
    ) -> List[TradeRecommendation]:
        """
        Main entry point for analyzing trading opportunities with optional screening.

        Args:
            favorite_instruments: List of user's favorite trading instruments
            portfolio_data: Optional portfolio context for risk management
            skip_screening: If True, skip the screening step
            selected_instruments: If provided, analyze these specific instruments

        Returns:
            List of trade recommendations
        """
        try:
            # If specific instruments are provided, analyze them directly
            if selected_instruments:
                return await self.analyze_selected_instruments(selected_instruments, portfolio_data)

            # If screening is skipped, analyze all favorite instruments
            if skip_screening:
                return await self.analyze_selected_instruments(favorite_instruments, portfolio_data)

            # Otherwise, run the full screening workflow (backward compatibility)
            self.logger.info(f"Starting analysis for {len(favorite_instruments)} instruments")

            # Step 1: Screen instruments to select best opportunities
            screening_result = await self._screen_instruments(favorite_instruments)

            if not screening_result.recommended_instruments:
                self.logger.warning("No instruments recommended by screener")
                return []

            self.logger.info(f"Screener selected {len(screening_result.recommended_instruments)} instruments")

            # Step 2: Analyze each recommended instrument
            return await self.analyze_selected_instruments(screening_result.recommended_instruments, portfolio_data)

        except Exception as e:
            self.logger.error(f"Error in trading analysis pipeline: {str(e)}")
            return []

    async def _screen_instruments(self, instruments: List[TradingInstrument]):
        """Screen instruments to select best opportunities."""
        # Get basic market data for screening
        market_overview = {}
        for instrument in instruments[:10]:  # Limit for API efficiency
            try:
                market_data = await self.market_data_service.get_market_data(instrument)
                market_overview[instrument.symbol] = {
                    "current_price": market_data.current_price,
                    "volume": market_data.volume_24h,
                    "news_count": len(market_data.news_items)
                }
            except Exception as e:
                self.logger.warning(f"Error getting market data for {instrument.symbol}: {e}")
                continue

        context = {
            "favorite_instruments": instruments,
            "market_data": market_overview
        }

        return await self.screener_agent.analyze(context)

    @logfire.instrument("_analyze_instrument", extract_args=True)
    async def _analyze_instrument(
        self,
        instrument: TradingInstrument,
        portfolio_data: Optional[Dict] = None
    ) -> Optional[TradeRecommendation]:
        """Perform comprehensive analysis on a single instrument."""
        try:
            self.logger.info(f"Analyzing {instrument.symbol}")

            # Step 1: Gather market data
            with logfire.span("gather_market_data", symbol=instrument.symbol):
                market_data = await self.market_data_service.get_market_data(instrument)
                technical_data = await self.market_data_service.get_technical_data(instrument.symbol)
                fundamental_data = await self.market_data_service.get_fundamental_data(instrument.symbol)

            # Step 2: Run analyses in parallel for efficiency
            with logfire.span("parallel_agent_analysis", symbol=instrument.symbol):
                fundamental_task = self._run_fundamental_analysis(instrument, market_data, fundamental_data)
                technical_task = self._run_technical_analysis(instrument, market_data, technical_data)
                sentiment_task = self._run_sentiment_analysis(instrument, market_data)

                fundamental_analysis, technical_analysis, sentiment_analysis = await asyncio.gather(
                    fundamental_task, technical_task, sentiment_task,
                    return_exceptions=True
                )

            # Handle any analysis failures
            if isinstance(fundamental_analysis, Exception):
                self.logger.error(f"Fundamental analysis failed for {instrument.symbol}: {fundamental_analysis}")
                fundamental_analysis = None

            if isinstance(technical_analysis, Exception):
                self.logger.error(f"Technical analysis failed for {instrument.symbol}: {technical_analysis}")
                technical_analysis = None

            if isinstance(sentiment_analysis, Exception):
                self.logger.error(f"Sentiment analysis failed for {instrument.symbol}: {sentiment_analysis}")
                sentiment_analysis = None

            # Step 3: Risk analysis (depends on other analyses)
            with logfire.span("risk_analysis", symbol=instrument.symbol):
                risk_analysis = await self._run_risk_analysis(
                    instrument, market_data, portfolio_data,
                    fundamental_analysis, technical_analysis
                )

            # Step 4: Generate trade strategy
            with logfire.span("trade_strategy", symbol=instrument.symbol):
                trade_recommendation = await self._run_trade_strategy(
                    instrument, market_data,
                    fundamental_analysis, technical_analysis, sentiment_analysis, risk_analysis
                )

            if trade_recommendation:
                logfire.info(
                    "Comprehensive analysis completed",
                    symbol=instrument.symbol,
                    recommendation_score=trade_recommendation.overall_score,
                    direction=trade_recommendation.direction,
                    confidence=trade_recommendation.confidence_level
                )

            return trade_recommendation

        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis for {instrument.symbol}: {str(e)}")
            return None

    @logfire.instrument("run_fundamental_analysis", extract_args=True)
    async def _run_fundamental_analysis(self, instrument, market_data, fundamental_data):
        """Run fundamental analysis."""
        with logfire.span("fundamental_agent_context_preparation", symbol=instrument.symbol):
            context = {
                "symbol": instrument.symbol,
                "market_data": market_data.dict() if market_data else {},
                "financial_data": fundamental_data
            }
            logfire.info("Starting fundamental analysis", symbol=instrument.symbol)

        with logfire.span("fundamental_agent_execution", symbol=instrument.symbol):
            result = await self.fundamental_agent.analyze(context)
            logfire.info("Fundamental analysis completed",
                        symbol=instrument.symbol,
                        signal=getattr(result, 'signal', 'unknown'),
                        score=getattr(result, 'score', 0))
            return result

    @logfire.instrument("run_technical_analysis", extract_args=True)
    async def _run_technical_analysis(self, instrument, market_data, technical_data):
        """Run technical analysis."""
        with logfire.span("technical_agent_context_preparation", symbol=instrument.symbol):
            context = {
                "symbol": instrument.symbol,
                "price_data": [p.dict() for p in market_data.price_history] if market_data else [],
                "volume_data": technical_data.get("volume_data", []),
                "indicators": technical_data
            }
            logfire.info("Starting technical analysis",
                        symbol=instrument.symbol,
                        price_data_points=len(context["price_data"]),
                        indicators_count=len(technical_data))

        with logfire.span("technical_agent_execution", symbol=instrument.symbol):
            result = await self.technical_agent.analyze(context)
            logfire.info("Technical analysis completed",
                        symbol=instrument.symbol,
                        signal=getattr(result, 'signal', 'unknown'),
                        score=getattr(result, 'score', 0),
                        trend=getattr(result, 'trend_direction', 'unknown'))
            return result

    @logfire.instrument("run_sentiment_analysis", extract_args=True)
    async def _run_sentiment_analysis(self, instrument, market_data):
        """Run sentiment analysis."""
        with logfire.span("sentiment_agent_context_preparation", symbol=instrument.symbol):
            context = {
                "symbol": instrument.symbol,
                "news_items": market_data.news_items if market_data else [],
                "social_data": [],  # Could integrate social media APIs
                "analyst_data": {}  # Could integrate analyst rating APIs
            }
            logfire.info("Starting sentiment analysis",
                        symbol=instrument.symbol,
                        news_items_count=len(context["news_items"]))

        with logfire.span("sentiment_agent_execution", symbol=instrument.symbol):
            result = await self.sentiment_agent.analyze(context)
            logfire.info("Sentiment analysis completed",
                        symbol=instrument.symbol,
                        signal=getattr(result, 'signal', 'unknown'),
                        score=getattr(result, 'score', 0),
                        sentiment=getattr(result, 'overall_sentiment', 0))
            return result

    @logfire.instrument("run_risk_analysis", extract_args=True)
    async def _run_risk_analysis(self, instrument, market_data, portfolio_data,
                               fundamental_analysis, technical_analysis):
        """Run risk analysis."""
        with logfire.span("risk_agent_context_preparation", symbol=instrument.symbol):
            context = {
                "symbol": instrument.symbol,
                "market_data": market_data.dict() if market_data else {},
                "price_history": [p.dict() for p in market_data.price_history] if market_data else [],
                "portfolio_data": portfolio_data or {},
                "fundamental_analysis": fundamental_analysis,
                "technical_analysis": technical_analysis
            }
            logfire.info("Starting risk analysis",
                        symbol=instrument.symbol,
                        has_fundamental=fundamental_analysis is not None,
                        has_technical=technical_analysis is not None,
                        has_portfolio=portfolio_data is not None)

        with logfire.span("risk_agent_execution", symbol=instrument.symbol):
            result = await self.risk_agent.analyze(context)
            logfire.info("Risk analysis completed",
                        symbol=instrument.symbol,
                        risk_score=getattr(result, 'overall_risk_score', 0),
                        position_size=getattr(result, 'max_position_size', 0),
                        stop_loss=getattr(result, 'recommended_stop_loss', 0))
            return result

    @logfire.instrument("run_trade_strategy", extract_args=True)
    async def _run_trade_strategy(self, instrument, market_data,
                                fundamental_analysis, technical_analysis,
                                sentiment_analysis, risk_analysis):
        """Generate comprehensive trade strategy."""
        with logfire.span("trade_strategy_context_preparation", symbol=instrument.symbol):
            context = {
                "symbol": instrument.symbol,
                "market_data": market_data.dict() if market_data else {},
                "fundamental_analysis": fundamental_analysis,
                "technical_analysis": technical_analysis,
                "sentiment_analysis": sentiment_analysis,
                "risk_analysis": risk_analysis,
                "min_risk_reward_ratio": settings.min_risk_reward_ratio
            }
            logfire.info("Starting trade strategy generation",
                        symbol=instrument.symbol,
                        has_fundamental=fundamental_analysis is not None,
                        has_technical=technical_analysis is not None,
                        has_sentiment=sentiment_analysis is not None,
                        has_risk=risk_analysis is not None,
                        min_risk_reward=float(settings.min_risk_reward_ratio))

        with logfire.span("trade_strategy_execution", symbol=instrument.symbol):
            result = await self.trade_strategy_agent.analyze(context)
            if result:
                logfire.info("Trade strategy completed",
                            symbol=instrument.symbol,
                            direction=getattr(result, 'direction', 'unknown'),
                            overall_score=getattr(result, 'overall_score', 0),
                            confidence=getattr(result, 'confidence_level', 0),
                            entry_price=float(getattr(result.entry, 'price', 0)) if hasattr(result, 'entry') else 0)
            return result

    async def close(self):
        """Clean up resources."""
        await self.market_data_service.close()
        self.logger.info("Trading orchestrator closed")