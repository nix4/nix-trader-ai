"""Base agent class for all trading agents."""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Generic, TypeVar

import logfire
from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent

from .config import settings

T = TypeVar('T', bound=BaseModel)


class BaseAgent(ABC, Generic[T]):
    """Base class for all trading agents."""

    def __init__(self, name: str, description: str):
        """Initialize the base agent."""
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.logger = logger.bind(agent=name)

        # Initialize pydantic-ai agent with explicit API key
        import os
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key

        # Create agent with output type for structured output
        self.agent = Agent(
            model=settings.ai_model,
            output_type=self.get_result_type(),
            system_prompt=self.get_system_prompt(),
        )

        self.logger.info(f"Initialized {name} agent")

    @abstractmethod
    def get_result_type(self) -> type[T]:
        """Return the result type for this agent."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> T:
        """Perform the agent's analysis."""
        pass

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "model": settings.ai_model,
        }

    @logfire.instrument("run_agent", extract_args=True)
    async def _run_agent(self, user_prompt: str, context: Dict[str, Any] = None) -> T:
        """Run the pydantic-ai agent with the given prompt."""
        try:
            self.logger.info(f"Running {self.name} agent with prompt: {user_prompt[:100]}...")

            with logfire.span(f"{self.name.lower()}_agent_execution"):
                logfire.info(
                    f"Starting {self.name} agent",
                    agent=self.name,
                    prompt_length=len(user_prompt),
                    context_keys=list(context.keys()) if context else []
                )

                # Prepare the context for the agent
                agent_context = context or {}

                # Run the agent and get the response
                result = await self.agent.run(
                    user_prompt,
                    deps=agent_context
                )

            self.logger.info(f"{self.name} agent completed successfully")
            logfire.info(f"{self.name} agent completed", agent=self.name, success=True)

            # pydantic-ai returns structured data in result.data when result_type is specified
            if hasattr(result, 'data'):
                return result.data
            else:
                # Fallback to output if data is not available
                return result.output if hasattr(result, 'output') else result

        except Exception as e:
            self.logger.error(f"Error in {self.name} agent: {str(e)}")
            # Create a fallback response for debugging
            result_type = self.get_result_type()
            try:
                # Get the result type name to create appropriate fallback
                result_name = result_type.__name__

                if result_name == "FundamentalAnalysis":
                    return result_type(
                        symbol=context.get('symbol', 'ERROR'),
                        signal="hold",
                        score=0.0,
                        reasoning=f"Agent error: {str(e)}",
                        analyzed_at=datetime.now()
                    )
                elif result_name == "TechnicalAnalysis":
                    return result_type(
                        symbol=context.get('symbol', 'ERROR'),
                        indicators=[],
                        trend_direction="unknown",
                        signal="hold",
                        score=0.0,
                        reasoning=f"Agent error: {str(e)}",
                        analyzed_at=datetime.now()
                    )
                elif result_name == "SentimentAnalysis":
                    return result_type(
                        symbol=context.get('symbol', 'ERROR'),
                        overall_sentiment=0.0,
                        news_sentiment=0.0,
                        sentiment_sources=0,
                        signal="hold",
                        score=0.0,
                        reasoning=f"Agent error: {str(e)}",
                        key_themes=[],
                        analyzed_at=datetime.now()
                    )
                elif result_name == "RiskAnalysis":
                    return result_type(
                        symbol=context.get('symbol', 'ERROR'),
                        overall_risk_score=50.0,
                        volatility_risk=50.0,
                        liquidity_risk=50.0,
                        market_risk=50.0,
                        fundamental_risk=50.0,
                        risk_factors=[],
                        max_position_size=Decimal("1.0"),
                        recommended_stop_loss=Decimal("5.0"),
                        reasoning=f"Agent error: {str(e)}",
                        analyzed_at=datetime.now()
                    )
                elif result_name == "TradeRecommendation":
                    from ..models.trade import TradeDirection, TradeTimeframe, TradeEntry, TradeExit, TradeRisk
                    return result_type(
                        symbol=context.get('symbol', 'ERROR'),
                        direction=TradeDirection.LONG,
                        timeframe=TradeTimeframe.SWING,
                        entry=TradeEntry(
                            price=Decimal("100.0"),
                            quantity=100,
                            confidence=50.0
                        ),
                        exit=TradeExit(
                            stop_loss=Decimal("95.0"),
                            take_profit=[Decimal("110.0")],
                            stop_loss_percent=Decimal("5.0"),
                            take_profit_percents=[Decimal("10.0")]
                        ),
                        risk=TradeRisk(
                            risk_reward_ratio=Decimal("2.0"),
                            position_size_percent=Decimal("1.0"),
                            max_loss_amount=Decimal("500.0"),
                            max_gain_amount=Decimal("1000.0"),
                            probability_of_success=0.5,
                            risk_level="high"
                        ),
                        overall_score=0.0,
                        confidence_level=0.0,
                        reasoning=f"Agent error: {str(e)}",
                        key_factors=["Error in analysis"],
                        risks=["Analysis failed"],
                        created_at=datetime.now()
                    )
                else:
                    # Generic fallback - just raise the error
                    raise e
            except Exception as fallback_error:
                self.logger.error(f"Could not create fallback response: {fallback_error}")
                raise e

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.name} Agent"

    def __repr__(self) -> str:
        """Detailed representation of the agent."""
        return f"<{self.__class__.__name__}(name='{self.name}')>"