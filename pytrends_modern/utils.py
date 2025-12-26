"""
Utility functions for pytrends-modern
"""

from datetime import date, datetime, timedelta
from typing import Optional, Tuple

import pandas as pd


def convert_dates_to_timeframe(start: date, stop: date) -> str:
    """
    Convert two dates to Google Trends timeframe string

    Args:
        start: Start date
        stop: End date

    Returns:
        Timeframe string (e.g., "2023-01-01 2023-12-31")

    Example:
        >>> from datetime import date
        >>> timeframe = convert_dates_to_timeframe(
        ...     date(2023, 1, 1),
        ...     date(2023, 12, 31)
        ... )
        >>> print(timeframe)
        2023-01-01 2023-12-31
    """
    return f"{start.strftime('%Y-%m-%d')} {stop.strftime('%Y-%m-%d')}"


def parse_timeframe(timeframe: str) -> Optional[Tuple[datetime, datetime]]:
    """
    Parse a timeframe string to start and end dates

    Args:
        timeframe: Timeframe string (e.g., "today 12-m", "2023-01-01 2023-12-31")

    Returns:
        Tuple of (start_datetime, end_datetime) or None if relative timeframe

    Example:
        >>> dates = parse_timeframe("2023-01-01 2023-12-31")
        >>> print(dates)
        (datetime(2023, 1, 1), datetime(2023, 12, 31))
    """
    # Check if it's a date range
    if " " in timeframe and not timeframe.startswith(("now", "today")):
        parts = timeframe.split()
        if len(parts) == 2:
            try:
                start = datetime.strptime(parts[0], "%Y-%m-%d")
                end = datetime.strptime(parts[1], "%Y-%m-%d")
                return (start, end)
            except ValueError:
                pass

    return None


def validate_keywords(keywords: list) -> bool:
    """
    Validate keyword list

    Args:
        keywords: List of keywords

    Returns:
        True if valid

    Raises:
        ValueError: If keywords are invalid
    """
    if not keywords:
        raise ValueError("At least one keyword is required")

    if len(keywords) > 5:
        raise ValueError("Maximum 5 keywords allowed")

    for kw in keywords:
        if not isinstance(kw, str):
            raise ValueError(f"Keywords must be strings, got {type(kw)}")
        if not kw.strip():
            raise ValueError("Keywords cannot be empty")

    return True


def normalize_geo_code(geo: str) -> str:
    """
    Normalize geographic code to uppercase

    Args:
        geo: Geographic code

    Returns:
        Uppercase geo code

    Example:
        >>> normalize_geo_code('us')
        'US'
        >>> normalize_geo_code('US-ca')
        'US-CA'
    """
    return geo.upper()


def format_traffic_number(traffic: int) -> str:
    """
    Format traffic number with comma separators

    Args:
        traffic: Traffic count

    Returns:
        Formatted string (e.g., "1,000,000+")

    Example:
        >>> format_traffic_number(1000000)
        '1,000,000+'
    """
    if traffic >= 1000000:
        return f"{traffic:,}+"
    elif traffic >= 1000:
        return f"{traffic:,}"
    else:
        return str(traffic)


def merge_trends_data(dfs: list, how: str = "outer") -> pd.DataFrame:
    """
    Merge multiple trends DataFrames

    Args:
        dfs: List of DataFrames to merge
        how: Merge method ('outer', 'inner', 'left', 'right')

    Returns:
        Merged DataFrame

    Example:
        >>> df1 = pytrends1.interest_over_time()
        >>> df2 = pytrends2.interest_over_time()
        >>> merged = merge_trends_data([df1, df2])
    """
    if not dfs:
        return pd.DataFrame()

    result = dfs[0]
    for df in dfs[1:]:
        result = pd.merge(
            result, df, left_index=True, right_index=True, how=how, suffixes=("", "_dup")
        )

    return result


def calculate_trend_momentum(df: pd.DataFrame, keyword: str, window: int = 7) -> pd.Series:
    """
    Calculate momentum (rate of change) for a keyword's trend

    Args:
        df: DataFrame from interest_over_time()
        keyword: Keyword column to analyze
        window: Window size for rolling average

    Returns:
        Series with momentum values

    Example:
        >>> df = pytrends.interest_over_time()
        >>> momentum = calculate_trend_momentum(df, 'Python', window=7)
        >>> print(momentum.tail())
    """
    if keyword not in df.columns:
        raise ValueError(f"Keyword '{keyword}' not found in DataFrame")

    # Calculate rolling average
    rolling_avg = df[keyword].rolling(window=window).mean()

    # Calculate momentum (percent change)
    momentum = rolling_avg.pct_change() * 100

    return momentum


def detect_trend_spikes(df: pd.DataFrame, keyword: str, threshold: float = 2.0) -> pd.DataFrame:
    """
    Detect significant spikes in trend data

    Args:
        df: DataFrame from interest_over_time()
        keyword: Keyword column to analyze
        threshold: Standard deviations above mean to consider a spike

    Returns:
        DataFrame with only spike periods

    Example:
        >>> df = pytrends.interest_over_time()
        >>> spikes = detect_trend_spikes(df, 'Python', threshold=2.0)
        >>> print(spikes)
    """
    if keyword not in df.columns:
        raise ValueError(f"Keyword '{keyword}' not found in DataFrame")

    series = df[keyword]
    mean = series.mean()
    std = series.std()

    # Find values above threshold
    threshold_value = mean + (threshold * std)
    spikes = df[series > threshold_value]

    return spikes


def export_to_multiple_formats(
    df: pd.DataFrame, base_path: str, formats: list = ["csv", "json", "parquet"]
) -> dict:
    """
    Export DataFrame to multiple formats

    Args:
        df: DataFrame to export
        base_path: Base path without extension (e.g., "trends")
        formats: List of formats to export to

    Returns:
        Dictionary mapping format to file path

    Example:
        >>> df = pytrends.interest_over_time()
        >>> paths = export_to_multiple_formats(df, "my_trends")
        >>> print(paths)
        {'csv': 'my_trends.csv', 'json': 'my_trends.json', ...}
    """
    results = {}

    for fmt in formats:
        path = f"{base_path}.{fmt}"

        if fmt == "csv":
            df.to_csv(path)
        elif fmt == "json":
            df.to_json(path, orient="records", date_format="iso")
        elif fmt == "parquet":
            try:
                df.to_parquet(path)
            except ImportError:
                print(f"Warning: pyarrow not installed, skipping parquet export")
                continue
        elif fmt == "excel" or fmt == "xlsx":
            try:
                df.to_excel(path)
            except ImportError:
                print(f"Warning: openpyxl not installed, skipping Excel export")
                continue
        else:
            print(f"Warning: Unknown format '{fmt}', skipping")
            continue

        results[fmt] = path

    return results
