import logging
from datetime import date, timedelta

import numpy as np
import pandas as pd

from services.model import ForecastResult

from services.yahoo_finance_client import YahooFinanceClient


class PredictionService:
    def __init__(self):
        self.yahoo_finance_client = YahooFinanceClient()
        self.number_of_future_trading_days = 5
        self.k = 10  # number of past days to consider when calculating average.

    @staticmethod
    def _roll_forward_forecast(last_known_prices: list[float], window: int, steps: int) -> list[float]:
        """Recursive MA forecast: each next-day price = mean of last K observations (where after t0 we append our own predictions)."""
        prices = list(last_known_prices)
        preds = []
        for _ in range(steps):
            if len(prices) < window:
                raise ValueError("insufficient window length for forecasting")
            next_price = float(np.mean(prices[-window:]))
            preds.append(next_price)
            prices.append(next_price)
        return preds


    @staticmethod
    def _cumulative_return(current_price: float, future_prices: list[float]) -> float:
        if not future_prices:
            return 0.0
        end_price = future_prices[-1]
        return (end_price / current_price) - 1.0
    
    @staticmethod
    def _calculate_confidence(s_close, i_close, spread, lookback_days, horizon_days):
        # A simple confidence heuristic: scaled absolute spread by expected volatility proxy.
        # Use recent (K) realized volatility of stock-index spread as a denominator; map via logistic to 0..1.
        spread_hist = (s_close.pct_change() - i_close.pct_change()).dropna().tail(lookback_days)
        denom = max(spread_hist.std(), 1e-4)
        z = float(abs(spread) / (denom * np.sqrt(horizon_days))) # scale with horizon
        confidence = float(1.0 / (1.0 + np.exp(-z))) # sigmoid
        return confidence
    
    @staticmethod
    def _calculate_future_prediction(stock_close: pd.Series, sp500_close: pd.Series, lookback_days: int, horizon_days: int):
        stock_latest_close_value = float(stock_close.iloc[-1])
        sp500_latest_close_value = float(sp500_close.iloc[-1])

        stock_pred_path = PredictionService._roll_forward_forecast(stock_close.tolist(), window=lookback_days, steps=horizon_days)
        sp500_pred_path = PredictionService._roll_forward_forecast(sp500_close.tolist(), window=lookback_days, steps=horizon_days)

        stock_cumulative = PredictionService._cumulative_return(stock_latest_close_value, stock_pred_path)
        sp500_cumulative = PredictionService._cumulative_return(sp500_latest_close_value, sp500_pred_path)

        return stock_cumulative, sp500_cumulative


    def predict(self, symbol: str, requested_date: date, lookback_days: int | None = None, horizon_days: int | None = None) -> ForecastResult:
        """
        Generates a stock movement prediction based on historical data.

        :param symbol: The stock ticker symbol.
        :param requested_date: The date for the prediction.
        :param lookback_days: The number of past trading days to consider.
        :param horizon_days: The number of future trading days to forecast.
        :return: A ForecastResult object with the prediction result and confidence score.
        """       
        logging.info(f"Generating prediction for {symbol} on {requested_date.isoformat()}.")
        lookback_days = lookback_days or self.k
        horizon_days = horizon_days or self.number_of_future_trading_days
        # To ensure we get enough trading days, fetch a larger window of calendar days.
        start_date = requested_date - timedelta(days=lookback_days * 2 + 5)
        # yfinance `end` parameter is exclusive, so add one day to include the requested date.
        end_date = requested_date + timedelta(days=1)

        logging.info(f"Fetching data for {symbol} from {start_date.isoformat()} to {end_date.isoformat()}")
        try:
            sp500_data, stock_data = self.yahoo_finance_client.fetch_ohlcv_data(
                ticker_symbol=symbol,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
        except:
            return ForecastResult(prediction=False, confidence=0.0)

        if stock_data is None:
            logging.error(f"Could not fetch data for {symbol}.")
            return ForecastResult(prediction=False, confidence=0.0)


        # Filter data to be on or before the requested date, as yfinance might return more.
        stock_data = stock_data[stock_data.index.date <= requested_date]
        sp500_data = sp500_data[sp500_data.index.date <= requested_date]

        if len(stock_data) < lookback_days:
            logging.warning(f"Not enough historical data for {symbol}. Found {len(stock_data)} days, need {lookback_days}.")
            return ForecastResult(prediction=False, confidence=0.0)

        last_k_days_data = stock_data.sort_index().tail(lookback_days)
        last_k_days_sp500 = sp500_data.sort_index().tail(lookback_days)
        
        stock_close = last_k_days_data["Close"]
        sp500_close = last_k_days_sp500["Close"]

        stock_cumulative, sp500_cumulative = PredictionService._calculate_future_prediction(stock_close, sp500_close, lookback_days, horizon_days)

        spread = stock_cumulative - sp500_cumulative
        outperform = spread > 0
        confidence_score = self._calculate_confidence(stock_close, sp500_close, spread, lookback_days, horizon_days)

        return ForecastResult(
            prediction=outperform,
            confidence=confidence_score
        )
