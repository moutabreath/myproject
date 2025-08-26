import logging
import os
from flask_pydantic import validate
from flask import Flask, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException
from asgiref.wsgi import WsgiToAsgi

from api.models import PredictionRequest, PredictionResponse
from outward_services.exceptions import TickerNotFoundError
from services.prediction_service import PredictionService
from util.logger import setup_logging

app = Flask(__name__)
# Wrap the Flask app with ASGI middleware
asgi_app = WsgiToAsgi(app)

logger = setup_logging(logging.INFO)

class PredictionError(Exception):
    """Custom exception for application-specific errors."""
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

 # --- Global Error Handler ---
@app.errorhandler(Exception)
def handle_exception(e):
    """General error handler for unhandled exceptions."""
    # Let Werkzeug/Flask HTTP errors keep their intended status codes
    if isinstance(e, HTTPException):
        return jsonify({"error": e.name, "message": e.description}), e.code

    if isinstance(e, PredictionError):
        logger.error(f"Prediction Error: {e.message} (Status: {e.status_code})")
        return jsonify({"error": e.message}), e.status_code
    if isinstance(e, ValidationError):
         error_details = [{"loc": err["loc"], "msg": err["msg"]} for err in e.errors()]
         logger.warning(f"Validation Error: {error_details}")
         return jsonify({"error": "Invalid request body", "details": error_details}), 400

    if isinstance(e, TickerNotFoundError):
        logger.warning(f"Invalid ticker symbol: {e.symbol}")
        return jsonify({
            "error": "Invalid ticker symbol",
            "message": str(e),
            "symbol": e.symbol
        }), 400

    logger.exception("An unexpected error occurred.")
    return jsonify({"error": "An unexpected server error occurred."}), 500

@app.route('/predict', methods=['POST'])
@validate()
def predict(body: PredictionRequest) -> PredictionResponse:
    """
    POST endpoint to get a stock prediction.

    :param body: The validated PredictionRequest object containing symbol and date.
    :return: A JSON response conforming to the PredictionResponse model.
    """
    prediction_service = PredictionService()
    body.symbol = body.symbol.upper() # Standardize symbol
    date_str = body.date.strftime('%Y-%m-%d')
    logger.info(f"Received prediction request for symbol: {body.symbol} on date: {date_str}")
    forecast_result= prediction_service.predict(body.symbol, body.date)
    prediction_response = PredictionResponse(
        symbol=body.symbol,
        date=body.date,
        prediction=forecast_result.prediction,
        confidence=forecast_result.confidence)
    logger.info(f"Successfully processed request for {body.symbol}. Confidence: {prediction_response.confidence}")
    return prediction_response

if __name__ == '__main__':
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "127.0.0.1")
    
    if debug:
        app.run(debug=True, host=host, port=port)
    else:
        # In production mode, use Uvicorn
        import uvicorn
        uvicorn.run(
            asgi_app,
            host=host,
            port=port,
            log_level="info"
        )
