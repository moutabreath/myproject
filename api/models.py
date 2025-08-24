from datetime import date as dt_date
from pydantic import BaseModel, Field

# --- Request Validation Model ---
class PredictionRequest(BaseModel):
    """
    Model for the POST /predict request body.
    Ensures 'symbol' is a string and 'date' is a valid YYYY-MM-DD date.
    """
    symbol: str = Field(..., description="Stock ticker symbol, e.g., 'AAPL'.")
    date: dt_date = Field(..., description="Date for prediction in 'YYYY-MM-DD' format.")

# --- Response Model ---
class PredictionResponse(BaseModel):
    """
    Model for the POST /predict response body.
    Ensures 'confidence' is between 0.0 and 1.0.
    """
    symbol: str = Field(..., description="Stock ticker symbol.")
    date: dt_date = Field(..., description="Date of prediction.")
    prediction: bool = Field(..., description="The predicted outcome (True/False).")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level of the prediction.")