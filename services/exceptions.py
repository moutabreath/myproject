"""Custom exceptions for the prediction service and its clients."""


class ServiceError(Exception):
    """Base exception for service-level errors."""
    pass


class TickerNotFoundError(ServiceError):
    """Raised when a stock ticker cannot be found or has no data in the range."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Ticker symbol '{symbol}' not found or has no data for the given range.")


class InsufficientDataError(ServiceError):
    """Raised when there is not enough historical data for a prediction."""

    def __init__(self, symbol: str, required: int, found: int):
        self.symbol = symbol
        self.required = required
        self.found = found
        super().__init__(f"Insufficient data for '{symbol}'. Required {required} trading days, but found {found}.")


class DataFetchError(ServiceError):
    """Raised when there is a network or other error fetching data."""

    def __init__(self, symbol: str):
        super().__init__(f"A network error or other issue occurred while fetching data for '{symbol}'.")