"""FastAPI application for the trading platform."""

from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..core.config import settings
from ..core.orchestrator import TradingOrchestrator
from ..models import TradingInstrument
from ..models.trade import TradeRecommendation
from .models import AnalysisRequest, AnalysisResponse


# Global orchestrator instance
orchestrator: TradingOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global orchestrator

    # Startup
    orchestrator = TradingOrchestrator()
    yield

    # Shutdown
    if orchestrator:
        await orchestrator.close()


app = FastAPI(
    title="Nix Trader AI",
    description="Production-ready multi-agent trading application framework",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Nix Trader AI - Multi-Agent Trading Platform",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_trading_opportunities(request: AnalysisRequest):
    """
    Analyze trading opportunities for the provided instruments.

    This endpoint orchestrates the complete analysis pipeline:
    1. Screens favorite instruments
    2. Performs fundamental, technical, and sentiment analysis
    3. Conducts risk analysis
    4. Generates trade recommendations
    """
    try:
        if not request.favorite_instruments:
            raise HTTPException(status_code=400, detail="No instruments provided")

        # Convert request instruments to domain models
        instruments = [
            TradingInstrument(**instrument.dict())
            for instrument in request.favorite_instruments
        ]

        # Run analysis pipeline
        recommendations = await orchestrator.analyze_trading_opportunities(
            favorite_instruments=instruments,
            portfolio_data=request.portfolio_data
        )

        return AnalysisResponse(
            recommendations=recommendations,
            total_analyzed=len(instruments),
            total_recommended=len(recommendations),
            analysis_timestamp="2024-01-01T00:00:00Z"  # Will be updated with actual timestamp
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/instruments/sample")
async def get_sample_instruments():
    """Get sample favorite instruments for testing."""
    return [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "instrument_type": "stock",
            "exchange": "NASDAQ",
            "currency": "USD",
            "sector": "Technology",
            "is_favorite": True
        },
        {
            "symbol": "GOOGL",
            "name": "Alphabet Inc.",
            "instrument_type": "stock",
            "exchange": "NASDAQ",
            "currency": "USD",
            "sector": "Technology",
            "is_favorite": True
        },
        {
            "symbol": "TSLA",
            "name": "Tesla Inc.",
            "instrument_type": "stock",
            "exchange": "NASDAQ",
            "currency": "USD",
            "sector": "Consumer Cyclical",
            "is_favorite": True
        }
    ]


@app.get("/agents/info")
async def get_agents_info():
    """Get information about available agents."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    return {
        "screener": orchestrator.screener_agent.get_agent_info(),
        "fundamental": orchestrator.fundamental_agent.get_agent_info(),
        "technical": orchestrator.technical_agent.get_agent_info(),
        "sentiment": orchestrator.sentiment_agent.get_agent_info(),
        "risk": orchestrator.risk_agent.get_agent_info(),
        "trade_strategy": orchestrator.trade_strategy_agent.get_agent_info(),
    }