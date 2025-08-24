import logging
import yfinance as yf
import pandas as pd
from typing import Optional, Tuple

class YahooFinanceClient:
    def __init__(self):
        self.index_ticker = '^GSPC' # S&P 500 index
        self.sp500_data = None
        self.recent_sp500_day = None

    def fetch_ohlcv_data(self, ticker_symbol: str, start_date: str, end_date: str) -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Fetches historical OHLCV data for a given ticker symbol and the S&P 500 index from Yahoo Finance.

        :param ticker_symbol: The stock ticker symbol (e.g., 'AAPL').
        :param start_date: The start date in 'YYYY-MM-DD' format.
        :param end_date: The end date in 'YYYY-MM-DD' format.
        :return: A tuple containing two pandas DataFrames: (sp500_data, stock_data), or None if an error occurs.
        """
        try:
            # Download both stock and index data in a single call for efficiency
            all_data = yf.download([ticker_symbol, self.index_ticker], start=start_date, end=end_date, group_by='ticker')
            
            if all_data.empty:
                logging.warning(f"No data found for tickers {ticker_symbol}, {self.index_ticker} in the specified date range.")
                return None

            stock_data = all_data[ticker_symbol]
            sp500_data = all_data[self.index_ticker]

            # Drop rows where all values are NaN, which can happen if a ticker has no data for a period
            stock_data.dropna(how='all', inplace=True)
            sp500_data.dropna(how='all', inplace=True)

            if stock_data.empty:
                logging.warning(f"No data found for {ticker_symbol} in the specified date range.")
                return None
            
            if sp500_data.empty:
                logging.warning(f"No data found for S&P 500 index ({self.index_ticker}) in the specified date range.")
                return None

            # Store S&P 500 data and the most recent day
            self.sp500_data = sp500_data
            self.recent_sp500_day = sp500_data.index[-1]

            stock_data.index.name = 'Date'
            sp500_data.index.name = 'Date'
            
            logging.debug(f"Successfully fetched data for {ticker_symbol} and {self.index_ticker}.")
            return sp500_data, stock_data

        except Exception as e:
            logging.error(f"An error occurred while fetching data for {ticker_symbol}: {e}", exc_info=True)
            return None
