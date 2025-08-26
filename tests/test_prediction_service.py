import pytest
from datetime import date, timedelta
from unittest.mock import patch
import pandas as pd

from services.prediction_service import PredictionService
from services.model import ForecastResult

@pytest.fixture
def prediction_service():
    """Create a PredictionService instance for testing."""
    return PredictionService()

@pytest.fixture
def mock_market_data():
    """Create mock market data for testing."""
    test_date = date.today()
    dates = [test_date - timedelta(days=x) for x in range(15)]
    
    sp500_data = pd.DataFrame({
        'Close': [100.0] * 15,
        'Date': dates
    }).set_index('Date')
    
    stock_data = pd.DataFrame({
        'Close': [200.0] * 15,
        'Date': dates
    }).set_index('Date')
    
    return sp500_data, stock_data

def test_prediction_service_predict(prediction_service, mock_market_data):
    """Test PredictionService.predict method with sufficient data."""
    test_date = date.today()
    test_symbol = "AAPL"
    sp500_data, stock_data = mock_market_data
    
    with patch('services.prediction_service.YahooFinanceClient') as mock_client:
        instance = mock_client.return_value
        instance.fetch_ohlcv_data.return_value = (sp500_data, stock_data)
        
        result = prediction_service.predict(test_symbol, test_date)
        
        assert isinstance(result, ForecastResult)
        assert isinstance(result.prediction, bool)
        assert isinstance(result.confidence, float)
        assert 0 <= result.confidence <= 1
        
        # Verify YahooFinanceClient was called correctly
        instance.fetch_ohlcv_data.assert_called_once()
        call_args = instance.fetch_ohlcv_data.call_args[1]
        assert call_args['ticker_symbol'] == test_symbol
        assert isinstance(call_args['start_date'], str)
        assert isinstance(call_args['end_date'], str)

def test_prediction_service_insufficient_data(prediction_service):
    """Test PredictionService behavior with insufficient historical data."""
    test_date = date.today()
    test_symbol = "AAPL"
    
    # Create data with insufficient history (less than required lookback days)
    dates = [test_date - timedelta(days=x) for x in range(5)]
    insufficient_data = pd.DataFrame({
        'Close': [100.0] * 5,
        'Date': dates
    }).set_index('Date')
    
    with patch('services.prediction_service.YahooFinanceClient') as mock_client:
        instance = mock_client.return_value
        instance.fetch_ohlcv_data.return_value = (insufficient_data, insufficient_data)
        
        result = prediction_service.predict(test_symbol, test_date)
        
        assert isinstance(result, ForecastResult)
        assert result.prediction is False
        assert result.confidence == 0.0

def test_prediction_service_data_fetch_error(prediction_service):
    """Test PredictionService behavior when data fetching fails."""
    test_date = date.today()
    test_symbol = "AAPL"
    
    with patch('services.prediction_service.YahooFinanceClient') as mock_client:
        instance = mock_client.return_value
        instance.fetch_ohlcv_data.side_effect = Exception("Simulated fetch error")
        
        result = prediction_service.predict(test_symbol, test_date)
        
        assert isinstance(result, ForecastResult)
        assert result.prediction is False
        assert result.confidence == 0.0

def test_roll_forward_forecast():
    """Test the rolling forecast calculation."""
    prices = [100.0, 101.0, 102.0, 103.0, 104.0]
    window = 3
    steps = 2
    
    forecasts = PredictionService._roll_forward_forecast(prices, window, steps)
    
    assert len(forecasts) == steps
    assert all(isinstance(x, float) for x in forecasts)
    # Test that forecast uses the correct window
    assert forecasts[0] == pytest.approx((102.0 + 103.0 + 104.0) / 3)

def test_cumulative_return():
    """Test cumulative return calculation."""
    current_price = 100.0
    future_prices = [101.0, 102.0, 103.0]
    
    returns = PredictionService._cumulative_return(current_price, future_prices)
    
    assert isinstance(returns, float)
    # Test the calculation: (final_price / initial_price) - 1
    assert returns == pytest.approx((103.0 / 100.0) - 1)

def test_calculate_confidence():
    """Test confidence score calculation."""
    dates = [date.today() - timedelta(days=x) for x in range(15)]
    stock_close = pd.Series([100.0 + x for x in range(15)], index=dates)
    index_close = pd.Series([100.0 + x*0.5 for x in range(15)], index=dates)
    spread = 0.05
    lookback_days = 10
    horizon_days = 5
    
    confidence = PredictionService._calculate_confidence(
        stock_close, 
        index_close, 
        spread, 
        lookback_days, 
        horizon_days
    )
    
    assert isinstance(confidence, float)
    assert 0 <= confidence <= 1
