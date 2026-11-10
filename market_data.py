import pandas as pd
import yfinance as yf

# Load stock data for a given ticker from Yahoo Finance and return a Pandas DataFrame
def load_data(ticker: str, start: str, end: str) -> pd.DataFrame: 
    # Download historical stock data for a given ticker symbol from Yahoo Finance library as a Pandas DataFrame
    # Adjust for stock splits and dividends, and don't show progress bar in console
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)

    # If the DataFrame has multi-level columns, keep only top-level columns ('Open', 'High', 'Low', 'Close', 'Volume')
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Clean data by dropping rows with missing values and columns not in the list
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

    # Convert row index from a string to a Pandas datetime object
    df.index = pd.to_datetime(df.index)

    # Sort dataframe rows by date (oldest to newest)
    return df.sort_index()

# Load CSV file from a given file path and return a Pandas DataFrame
def load_csv(path: str) -> pd.DataFrame:
    # Read CSV file into DataFrame, convert 'Date' column to datetime, and set it as the row index
    df = pd.read_csv(path, parse_dates=['Date'], index_col='Date')

    # Drop unused columns
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

    # Drop rows with missing values
    df = df.dropna()

    # Sort rows by date (oldest to newest)
    df = df.sort_index()

    return df

# Load stock data for all tickers in the list "tickers"
def load_all_tickers(tickers: list[str], start, end):
    # Create dictionary where each key is a ticker with a DataFrame as its value
    data_frames = {t: load_data(t, start, end) for t in tickers}

    # Create collection of dates (DatetimeIndex) from the DataFrame of the first ticker
    common_dates = data_frames[tickers[0]].index

    # Keep only the rows where the date appears in all tickers
    for df in data_frames:
        common_dates = common_dates.intersection(df.index)

    # Sort DatetimeIndex by date in ascending order
    common_dates = common_dates.sort_values()

    # Return dictionary of DataFrames with sorted dates
    return {t: df.loc[common_dates] for t, df in data_frames.items()}

