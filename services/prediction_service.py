import logging
from datetime import timedelta

from data.models import PredictionRequest, PredictionResponse
from services.yahoo_finance_client import YahooFinanceClient

logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(self):
        self.yahoo_finance_client = YahooFinanceClient()
        self.number_of_future_trading_days = 5
        self.k = 10  # number of past days to consider when calculating average.

    def predict(self, prediction_request: PredictionRequest) -> PredictionResponse:
        """
        Generates a stock movement prediction based on historical data.

        :param prediction_request: The request containing the stock symbol and date.
        :return: A PredictionResponse object with the prediction result.
        """
        requested_ticker = prediction_request.symbol
        requested_date = prediction_request.date

        # Fetch a slightly larger window (k + 7 days) to account for weekends and holidays.
        start_date = requested_date - timedelta(days=self.k + 7)

        logger.info(f"Fetching data for {requested_ticker} from {start_date} to {requested_date}")

        # Fetch historical data using our client
        data_result = self.yahoo_finance_client.fetch_ohlcv_data(
            ticker_symbol=requested_ticker,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=requested_date.strftime('%Y-%m-%d')
        )

        if not data_result:
            logger.error(f"Could not fetch data for {requested_ticker}.")
            return PredictionResponse(symbol=requested_ticker, date=requested_date, prediction=False, confidence=0.0)

        sp500_data, stock_data = data_result

        if len(stock_data) < self.k:
            logger.warning(f"Not enough historical data for {requested_ticker}. Found {len(stock_data)} days, need {self.k}.")
            return PredictionResponse(symbol=requested_ticker, date=requested_date, prediction=False, confidence=0.0)

        last_k_days_data = stock_data.sort_index().tail(self.k)
        average_close = last_k_days_data['Close'].mean()
        
        last_k_days_sp500 = sp500_data.sort_index().tail(self.k)
        average_sp500_close = last_k_days_sp500['Close'].mean()


        # Predict 'up' (True) if the latest close is above the average
        confidence_score = 0.75  # Placeholder confidence

        return PredictionResponse(
            symbol=requested_ticker,
            date=requested_date,
            prediction=average_close - average_sp500_close > 0,
            confidence=confidence_score
        )
