import pytest
from datetime import date
from typing import Generator
from unittest.mock import Mock, patch

from flask.testing import FlaskClient
from api.models import PredictionRequest, PredictionResponse
from services.model import ForecastResult
from app import app

@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def valid_request_data():
    """Create valid request data for testing."""
    return {
        "symbol": "AAPL",
        "date": date.today().isoformat()
    }

@pytest.fixture
def mock_prediction_service():
    """Create a mock PredictionService for testing."""
    with patch('app.PredictionService') as mock_service:
        service_instance = Mock()
        service_instance.predict.return_value = ForecastResult(
            prediction=True,
            confidence=0.75
        )
        mock_service.return_value = service_instance
        yield mock_service

def test_predict_endpoint_success(client, valid_request_data, mock_prediction_service):
    """Test successful prediction request."""
    response = client.post('/predict', json=valid_request_data)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['symbol'] == valid_request_data['symbol'].upper()
    assert data['prediction'] is True
    assert data['confidence'] == 0.75
    assert 'date' in data

def test_predict_endpoint_invalid_symbol(client, valid_request_data):
    """Test prediction request with invalid symbol."""
    valid_request_data['symbol'] = ""
    response = client.post('/predict', json=valid_request_data)
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'details' in data

def test_predict_endpoint_invalid_date(client, valid_request_data):
    """Test prediction request with invalid date."""
    valid_request_data['date'] = "invalid-date"
    response = client.post('/predict', json=valid_request_data)
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'details' in data

def test_predict_endpoint_missing_fields(client):
    """Test prediction request with missing required fields."""
    response = client.post('/predict', json={})
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'details' in data

def test_models():
    """Test Pydantic models validation."""
    # Test valid PredictionRequest
    request = PredictionRequest(
        symbol="AAPL",
        date=date.today()
    )
    assert request.symbol == "AAPL"
    assert isinstance(request.date, date)
    
    # Test valid PredictionResponse
    response = PredictionResponse(
        symbol="AAPL",
        date=date.today(),
        prediction=True,
        confidence=0.75
    )
    assert response.symbol == "AAPL"
    assert isinstance(response.date, date)
    assert response.prediction is True
    assert response.confidence == 0.75
