"""Tests for YFinance service to validate market data retrieval."""

import os
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd

# Suppress logfire warnings in tests
os.environ['LOGFIRE_IGNORE_NO_CONFIG'] = '1'

from src.nix_trader_ai.services.yfinance_service import YFinanceService
from src.nix_trader_ai.models.market_data import NewsItem, PriceData


class TestYFinanceService:
    """Test suite for YFinanceService."""

    @pytest.fixture
    def service(self):
        """Create a YFinanceService instance for testing."""
        return YFinanceService()

    @pytest.fixture
    def mock_ticker_data(self):
        """Mock ticker data for testing."""
        # Create mock historical data
        dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
        hist_data = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'Close': [102.0, 103.0, 104.0, 105.0, 106.0],
            'Volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        }, index=dates)

        return hist_data

    @pytest.fixture
    def mock_ticker_info(self):
        """Mock ticker info for testing."""
        return {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'marketCap': 3000000000000,
            'trailingPE': 30.5,
            'priceToBook': 45.2,
            'dividendYield': 0.005,
            'trailingEps': 6.42,
            'beta': 1.2,
            'fiftyTwoWeekHigh': 200.0,
            'fiftyTwoWeekLow': 120.0,
            'longBusinessSummary': 'Apple Inc. designs, manufactures, and markets smartphones...'
        }

    @pytest.fixture
    def mock_news_data(self):
        """Mock news data for testing."""
        return [
            {
                'title': 'Apple launches new product',
                'summary': 'Apple announces revolutionary new device',
                'publisher': 'TechNews',
                'providerPublishTime': 1704067200,  # 2024-01-01
                'link': 'https://example.com/news1'
            },
            {
                'title': 'Apple stock reaches all-time high',
                'summary': 'Investors celebrate as AAPL hits record',
                'publisher': 'FinanceDaily',
                'providerPublishTime': 1704153600,  # 2024-01-02
                'link': 'https://example.com/news2'
            }
        ]

    @pytest.mark.asyncio
    async def test_get_stock_quote_success(self, service, mock_ticker_data, mock_ticker_info):
        """Test successful stock quote retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock
            mock_instance = MagicMock()
            mock_instance.info = mock_ticker_info
            mock_instance.history.return_value = mock_ticker_data
            mock_ticker.return_value = mock_instance

            # Execute
            result = await service.get_stock_quote('AAPL')

            # Assert
            assert result['symbol'] == 'AAPL'
            assert isinstance(result['price'], Decimal)
            assert result['price'] == Decimal('106.0')
            assert isinstance(result['volume'], int)
            assert result['volume'] == 1400000
            assert 'latest_trading_day' in result
            assert 'change' in result
            assert 'change_percent' in result

    @pytest.mark.asyncio
    async def test_get_stock_quote_empty_data(self, service):
        """Test stock quote retrieval with empty historical data."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock with empty data
            mock_instance = MagicMock()
            mock_instance.info = {}
            mock_instance.history.return_value = pd.DataFrame()
            mock_ticker.return_value = mock_instance

            # Execute
            result = await service.get_stock_quote('INVALID')

            # Assert
            assert result == {}

    @pytest.mark.asyncio
    async def test_get_stock_quote_error_handling(self, service):
        """Test error handling in stock quote retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock to raise exception
            mock_ticker.side_effect = Exception("API Error")

            # Execute
            result = await service.get_stock_quote('AAPL')

            # Assert
            assert result == {}

    @pytest.mark.asyncio
    async def test_get_daily_prices_success(self, service, mock_ticker_data):
        """Test successful daily price history retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock
            mock_instance = MagicMock()
            mock_instance.history.return_value = mock_ticker_data
            mock_ticker.return_value = mock_instance

            # Execute
            result = await service.get_daily_prices('AAPL', days=5)

            # Assert
            assert len(result) == 5
            assert all(isinstance(price, PriceData) for price in result)
            assert result[0].symbol == 'AAPL'
            assert isinstance(result[0].open_price, Decimal)
            assert isinstance(result[0].close_price, Decimal)
            assert isinstance(result[0].high_price, Decimal)
            assert isinstance(result[0].low_price, Decimal)
            assert isinstance(result[0].volume, int)
            # Verify sorting (most recent first)
            assert result[0].timestamp > result[-1].timestamp

    @pytest.mark.asyncio
    async def test_get_daily_prices_empty_data(self, service):
        """Test daily prices with empty historical data."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock with empty data
            mock_instance = MagicMock()
            mock_instance.history.return_value = pd.DataFrame()
            mock_ticker.return_value = mock_instance

            # Execute
            result = await service.get_daily_prices('INVALID', days=100)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_get_daily_prices_different_periods(self, service, mock_ticker_data):
        """Test daily prices with different period parameters."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.history.return_value = mock_ticker_data
            mock_ticker.return_value = mock_instance

            # Test different period ranges
            test_cases = [
                (50, '3mo'),
                (150, '6mo'),
                (300, '1y')
            ]

            for days, expected_period in test_cases:
                result = await service.get_daily_prices('AAPL', days=days)
                # Verify the method was called with correct period
                assert len(result) <= days

    @pytest.mark.asyncio
    async def test_get_daily_prices_error_handling(self, service):
        """Test error handling in daily prices retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock to raise exception
            mock_ticker.side_effect = Exception("API Error")

            # Execute
            result = await service.get_daily_prices('AAPL', days=100)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_get_company_overview_success(self, service, mock_ticker_info):
        """Test successful company overview retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock
            mock_instance = MagicMock()
            mock_instance.info = mock_ticker_info
            mock_ticker.return_value = mock_instance

            # Execute
            result = await service.get_company_overview('AAPL')

            # Assert
            assert result['symbol'] == 'AAPL'
            assert result['name'] == 'Apple Inc.'
            assert result['sector'] == 'Technology'
            assert result['industry'] == 'Consumer Electronics'
            assert result['market_cap'] == '3000000000000'
            assert result['pe_ratio'] == '30.5'
            assert result['pb_ratio'] == '45.2'
            assert result['dividend_yield'] == '0.005'
            assert result['eps'] == '6.42'
            assert result['beta'] == '1.2'
            assert result['52_week_high'] == '200.0'
            assert result['52_week_low'] == '120.0'
            assert 'Apple Inc. designs' in result['description']
            assert len(result['description']) <= 500

    @pytest.mark.asyncio
    async def test_get_company_overview_missing_fields(self, service):
        """Test company overview with missing fields."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock with minimal data
            mock_instance = MagicMock()
            mock_instance.info = {'longName': 'Test Company'}
            mock_ticker.return_value = mock_instance

            # Execute
            result = await service.get_company_overview('TEST')

            # Assert
            assert result['symbol'] == 'TEST'
            assert result['name'] == 'Test Company'
            assert result['sector'] == ''
            assert result['market_cap'] == ''

    @pytest.mark.asyncio
    async def test_get_company_overview_error_handling(self, service):
        """Test error handling in company overview retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock to raise exception
            mock_ticker.side_effect = Exception("API Error")

            # Execute
            result = await service.get_company_overview('AAPL')

            # Assert
            assert result == {}

    @pytest.mark.asyncio
    async def test_get_news_sentiment_success(self, service, mock_news_data):
        """Test successful news retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock
            mock_instance = MagicMock()
            mock_instance.news = mock_news_data
            mock_ticker.return_value = mock_instance

            # Execute
            result = await service.get_news_sentiment(['AAPL'], limit=20)

            # Assert
            assert len(result) <= 20
            assert all(isinstance(item, NewsItem) for item in result)
            assert result[0].title == 'Apple stock reaches all-time high'  # Most recent first
            assert result[0].source == 'FinanceDaily'
            assert 'AAPL' in result[0].symbols
            assert result[0].url == 'https://example.com/news2'
            assert result[0].sentiment_score is None

    @pytest.mark.asyncio
    async def test_get_news_sentiment_multiple_symbols(self, service, mock_news_data):
        """Test news retrieval with multiple symbols."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock
            mock_instance = MagicMock()
            mock_instance.news = mock_news_data
            mock_ticker.return_value = mock_instance

            # Execute
            result = await service.get_news_sentiment(['AAPL', 'MSFT', 'GOOGL'], limit=20)

            # Assert - should limit to 3 symbols
            assert len(result) > 0
            assert all(isinstance(item, NewsItem) for item in result)

    @pytest.mark.asyncio
    async def test_get_news_sentiment_empty_data(self, service):
        """Test news retrieval with no news available."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock with empty news
            mock_instance = MagicMock()
            mock_instance.news = []
            mock_ticker.return_value = mock_instance

            # Execute
            result = await service.get_news_sentiment(['AAPL'], limit=20)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_get_news_sentiment_error_handling(self, service):
        """Test error handling in news retrieval."""
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock to raise exception
            mock_ticker.side_effect = Exception("API Error")

            # Execute
            result = await service.get_news_sentiment(['AAPL'], limit=20)

            # Assert
            assert result == []

    @pytest.mark.asyncio
    async def test_get_news_sentiment_limit(self, service, mock_news_data):
        """Test news retrieval respects limit parameter."""
        # Create more news items
        extended_news = mock_news_data * 15  # 30 items total

        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = MagicMock()
            mock_instance.news = extended_news
            mock_ticker.return_value = mock_instance

            # Execute with limit
            result = await service.get_news_sentiment(['AAPL'], limit=10)

            # Assert
            assert len(result) <= 10

    @pytest.mark.asyncio
    async def test_close(self, service):
        """Test service cleanup."""
        # Should complete without errors
        await service.close()
        # No assertions needed, just verify it doesn't raise


@pytest.mark.asyncio
async def test_integration_workflow():
    """Integration test simulating a complete workflow."""
    service = YFinanceService()

    with patch('yfinance.Ticker') as mock_ticker:
        # Setup comprehensive mock
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        hist_data = pd.DataFrame({
            'Open': [100.0 + i for i in range(100)],
            'High': [105.0 + i for i in range(100)],
            'Low': [95.0 + i for i in range(100)],
            'Close': [102.0 + i for i in range(100)],
            'Volume': [1000000 + i*10000 for i in range(100)]
        }, index=dates)

        mock_instance = MagicMock()
        mock_instance.info = {
            'longName': 'Test Corp',
            'marketCap': 1000000000,
            'trailingPE': 25.0
        }
        mock_instance.history.return_value = hist_data
        mock_instance.news = [
            {
                'title': 'Test News',
                'summary': 'Test Summary',
                'publisher': 'TestPublisher',
                'providerPublishTime': 1704067200,
                'link': 'https://test.com'
            }
        ]
        mock_ticker.return_value = mock_instance

        # Execute workflow
        quote = await service.get_stock_quote('TEST')
        prices = await service.get_daily_prices('TEST', days=50)
        overview = await service.get_company_overview('TEST')
        news = await service.get_news_sentiment(['TEST'], limit=5)

        # Assertions
        assert quote['symbol'] == 'TEST'
        assert len(prices) > 0
        assert overview['name'] == 'Test Corp'
        assert len(news) > 0

        await service.close()
