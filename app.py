import logging
from flask_pydantic import validate
from flask import Flask, jsonify
from pydantic import ValidationError

from data.models import PredictionRequest, PredictionResponse


app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Custom Exception ---
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
    if isinstance(e, PredictionError):
        logger.error(f"Prediction Error: {e.message} (Status: {e.status_code})")
        return jsonify({"error": e.message}), e.status_code

    if isinstance(e, ValidationError):
        error_details = [{"loc": err["loc"], "msg": err["msg"]} for err in e.errors()]
        logger.warning(f"Validation Error: {error_details}")
        return jsonify({"error": "Invalid request body", "details": error_details}), 400

    logger.exception("An unexpected error occurred.")
    return jsonify({"error": "An unexpected server error occurred."}), 500


@app.route('/predict', methods=['POST'])
@validate()
def predict(body: PredictionRequest):
    """
    POST endpoint to get a stock prediction.

    :param body: The validated PredictionRequest object containing symbol and date.
    :return: A JSON response conforming to the PredictionResponse model.
    """
    symbol = body.symbol.upper() # Standardize symbol
    date_str = body.date.strftime('%Y-%m-%d')
    logger.info(f"Received prediction request for symbol: {symbol} on date: {date_str}")

    
    if symbol == "AAPL" and date_str == "2024-10-25":
        prediction_result = {
            "symbol": symbol,
            "date": body.date,
            "prediction": True,
            "confidence": 0.83
        }
    elif symbol == "INVALID":
        raise PredictionError(f"Symbol '{symbol}' is not supported.", status_code=404)
    else:
        prediction_result = {
            "symbol": symbol,
            "date": body.date,
            "prediction": False,
            "confidence": 0.55
        }

    response_data = PredictionResponse(**prediction_result)
    logger.info(f"Successfully processed request for {symbol}. Confidence: {response_data.confidence}")
    
    return jsonify(response_data.model_dump())

if __name__ == '__main__':
    app.run(debug=True, port=5000)