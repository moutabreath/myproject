import logging
import yfinance as yf
import pandas as pd
from typing import Tuple

from .exceptions import DataFetchError, TickerNotFoundError

class YahooFinanceClient:
    def __init__(self):
        self.index_ticker = '^GSPC' # S&P 500 index
        self.sp500_data = None
        self.recent_sp500_day = None

    def fetch_ohlcv_data(self, ticker_symbol: str, start_date: str, end_date: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetches historical OHLCV data for a given ticker symbol and the S&P 500 index from Yahoo Finance.

        :param ticker_symbol: The stock ticker symbol (e.g., 'AAPL').
        :param start_date: The start date in 'YYYY-MM-DD' format.
        :param end_date: The end date in 'YYYY-MM-DD' format.
        :return: A tuple containing two pandas DataFrames: (sp500_data, stock_data).
        :raises TickerNotFoundError: If the ticker symbol is not found or has no data.
        :raises DataFetchError: If there is a network error or an issue fetching S&P 500 data.
        """
        try:
            yf.shared._ERRORS = {}

            # Download both stock and index data in a single call for efficiency
            all_data = yf.download(
                [ticker_symbol, self.index_ticker],
                start=start_date,
                end=end_date,
                group_by='ticker',
                progress=False  # Disable progress bar for cleaner logs
            )

            if ticker_symbol.upper() in yf.shared._ERRORS:
                error_msg = yf.shared._ERRORS[ticker_symbol.upper()]
                logging.warning(f"yfinance failed to download data for {ticker_symbol}: {error_msg}")
                raise TickerNotFoundError(symbol=ticker_symbol)

            if ticker_symbol not in all_data.columns or all_data[ticker_symbol].dropna(how='all').empty:
                logging.warning(f"No data found for {ticker_symbol} in the specified date range.")
                raise TickerNotFoundError(symbol=ticker_symbol)

            if self.index_ticker not in all_data.columns or all_data[self.index_ticker].dropna(how='all').empty:
                logging.error(f"Could not fetch required S&P 500 index data ({self.index_ticker}).")
                raise DataFetchError(symbol=self.index_ticker)

            stock_data = all_data[ticker_symbol].copy()
            sp500_data = all_data[self.index_ticker].copy()

            self.sp500_data = sp500_data
            self.recent_sp500_day = sp500_data.index[-1]

            stock_data.index.name = 'Date'
            sp500_data.index.name = 'Date'

            logging.debug(f"Successfully fetched data for {ticker_symbol} and {self.index_ticker}.")
            return sp500_data, stock_data

        except TickerNotFoundError:
            # Re-raise the specific exception to be caught by the service layer.
            raise
        except Exception as e:
            # Catch any other exception (network errors, etc.) and wrap it.
            logging.error(f"An unexpected error occurred while fetching data for {ticker_symbol}: {e}", exc_info=True)
            raise DataFetchError(symbol=ticker_symbol) from e
