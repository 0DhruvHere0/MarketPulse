import yfinance as yf
import pandas as pd
from backend.app.constants import MIN_ROWS_FOR_EMA200
class DataFetchError(Exception):
    def __init__(self, message: str, error_type: str = "unknown"):
        self.message = message
        self.error_type = error_type
        super().__init__(message)
def fetch_ohlcv(ticker: str, period: str = "1y") -> pd.DataFrame:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval="1d", auto_adjust=True)
        if df.empty:
            raise DataFetchError(f"No data found for ticker {ticker}", "no_data")
        if len(df) < MIN_ROWS_FOR_EMA200:
            raise DataFetchError(
                f"Insufficient data: {len(df)} rows (need >= {MIN_ROWS_FOR_EMA200})",
                "insufficient_data"
            )
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise DataFetchError(f"Missing columns: {missing}", "invalid_data")
        df = df[required_cols].dropna()
        if len(df) < MIN_ROWS_FOR_EMA200:
            raise DataFetchError(
                f"Insufficient valid data after cleaning: {len(df)} rows",
                "insufficient_data"
            )
        return df
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Failed to fetch data: {str(e)}", "fetch_error")
def get_ticker_info(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        return stock.info or {}
    except Exception:
        return {}
def get_company_name(ticker: str) -> str:
    info = get_ticker_info(ticker)
    return info.get('longName') or info.get('shortName') or ticker
def get_currency(ticker: str) -> str:
    info = get_ticker_info(ticker)
    return info.get('currency') or ''