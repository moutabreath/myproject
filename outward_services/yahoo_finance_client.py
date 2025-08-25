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
    
    # Robustly extract per-ticker frames regardless of yfinance/pandas layout
    @staticmethod
    def _extract(df: pd.DataFrame, symbol: str) -> pd.DataFrame | None:
        cols = df.columns
        if isinstance(cols, pd.MultiIndex):
            # Common case: ticker is level 0
            if symbol in cols.get_level_values(0):
                return df[symbol].copy()
            # Fallback: some versions place ticker at level 1
            if symbol in cols.get_level_values(1):
                return df.xs(symbol, axis=1, level=1, drop_level=True).copy()
            return None
        # Single-ticker shape (defensive)
        required = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
        return df.copy() if required.issubset(set(map(str, cols))) else None

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
            

            stock_data = YahooFinanceClient._extract(all_data, ticker_symbol)
            if stock_data is None or stock_data.dropna(how='all').empty:
                logging.warning(f"No data found for {ticker_symbol} in the specified date range.")
                raise TickerNotFoundError(symbol=ticker_symbol)

            sp500_data = YahooFinanceClient._extract(all_data, self.index_ticker)
            if sp500_data is None or sp500_data.dropna(how='all').empty:
                logging.error(f"Could not fetch required S&P 500 index data ({self.index_ticker}).")
                raise DataFetchError(symbol=self.index_ticker)

            self.sp500_data = sp500_data
            self.recent_sp500_day = sp500_data.index[-1]

            stock_data.index.name = 'Date'
            sp500_data.index.name = 'Date'
            return sp500_data, stock_data
        except TickerNotFoundError:
            raise
        except Exception as e:            
            logging.error(f"An unexpected error occurred while fetching data for {ticker_symbol}: {e}", exc_info=True)
            raise DataFetchError(symbol=ticker_symbol) from e
