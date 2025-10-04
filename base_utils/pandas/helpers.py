import pandas as pd
from loguru import logger
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression

"""
Miscenallaneous helper classes
"""


class StrValueEnum:
    def __init__(self, enum_class):
        self._enum_class = enum_class

    def __getattr__(self, name):
        return self._enum_class[name].value



def detrend_df(df: pd.DataFrame, center_on_mean: bool = False):
    """
    Remove linear trend from each column of a DataFrame.

    keep_level : if True, remove only the slope but keep the column mean
    """
    df = df.ffill()
    n = len(df)


    X = np.arange(n).reshape(-1, 1)
    df_detrended = pd.DataFrame(index=df.index, columns=df.columns)
    df_trend = pd.DataFrame(index=df.index, columns=df.columns)

    for col in df.columns:
        y = np.array(df[col].values)
        
        model = LinearRegression().fit(X, y)
        trend = model.predict(X)
        detrended = y - trend
        if center_on_mean:
            detrended += y.mean()
        df_detrended[col] = detrended
        df_trend[col] = trend

    return df_detrended



def index_slice(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Filters a multi-index DataFrame based on the provided key-value pairs using pd.xs.

    Parameters:
    - df (pd.DataFrame): Input DataFrame with multi-index columns.
    - **kwargs: Key-value pairs specifying levels and corresponding values to filter.
      Values can be a single value or a list of values.

    Returns:
    - pd.DataFrame: Filtered DataFrame.
    """
    filter_df = df.copy()

    for level, values in kwargs.items():
        if not isinstance(values, (list, tuple)):
            values = [values]

        # Filter columns using pd.xs for each value in the list
        slices = []
        for value in values:
            try:
                slice_df = filter_df.xs(value, level=level, axis=1, drop_level=False)
                slices.append(slice_df)
            except KeyError:
                logger.warning(f"Value '{value}' not found in level '{level}'.")

        if not slices:
            logger.warning(
                f"No matching values found for level '{level}'. Returning an empty DataFrame."
            )
            return pd.DataFrame()

        # Concatenate all slices
        filter_df: pd.DataFrame = pd.concat(slices, axis=1)
    return filter_df


def collapse_multi_index_cols(df: pd.DataFrame, join_str: str = "_") -> pd.DataFrame:
    """
    Collapse the vertical levels of a MultiIndex on the columns by concatenating the column levels.

    Args:
        df (pd.DataFrame): The DataFrame with a MultiIndex on columns.
        join_str (str): The string used to join the column index levels.

    Returns:
        pd.DataFrame: A DataFrame with collapsed MultiIndex columns.
    """
    if isinstance(df.columns, pd.MultiIndex):
        # Collapse the column index levels into a single level by joining with the join_str
        df.columns = [join_str.join(map(str, col)) for col in df.columns]

    return df


def keep_levels(df: pd.DataFrame, levels_to_keep) -> pd.DataFrame:
    """
    Retains only the specified levels in the MultiIndex columns of a DataFrame.

    Parameters:
        df (pd.DataFrame): Input DataFrame with MultiIndex columns.
        levels_to_keep (str or list): A level name or list of level names to retain in the MultiIndex.

    Returns:
        pd.DataFrame: A DataFrame with only the specified levels retained in the MultiIndex columns.
    """
    # Ensure the DataFrame has MultiIndex columns
    if not isinstance(df.columns, pd.MultiIndex):
        raise ValueError("The DataFrame does not have MultiIndex columns.")

    # Normalize levels_to_keep to a list
    if isinstance(levels_to_keep, str):
        levels_to_keep = [levels_to_keep]

    # Validate levels_to_keep
    column_levels = df.columns.names
    invalid_levels = [level for level in levels_to_keep if level not in column_levels]
    if invalid_levels:
        raise ValueError(
            f"Invalid levels specified: {invalid_levels}. Available levels are: {column_levels}"
        )

    # Retain only the specified levels
    retained_columns = df.columns.droplevel(
        [level for level in column_levels if level not in levels_to_keep]
    )
    return df.copy().set_axis(retained_columns, axis=1)


MONTH_MAP = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}


def _safe_replace_year(date, new_year):
    """Helper function to safely replace year, returning None if date doesn't exist in target year"""
    try:
        return date.replace(year=new_year)
    except ValueError:
        return None


def create_seasonal_df(
    df: pd.DataFrame | pd.Series, benchmark_year: int = datetime.now().year
) -> pd.DataFrame:
    """Pivot time series df to daily seasonal df. Note: the benchmark_year is default to the current year,
    if benchmark_year is not a leap year, historical Feb 29 will be dropped. This is an intentional choice over having
    benchmark_year always be a leap year, which creates confusion in the index of the seasonal_df

    Args:
        df: DateTimeIndex time series df. No multiIndex columns.
        benchmark_year (int, optional): current year

    Returns:
        df: rows = days of benchmark year, cols = [measure, year]
    """
    df = pd.DataFrame(df)

    benchmark_start_date, benchmark_end_date = (
        f"{benchmark_year}-01-01",
        f"{benchmark_year}-12-31",
    )
    benchmark_index = pd.date_range(start=benchmark_start_date, end=benchmark_end_date, freq=df.index.freqstr)  # type: ignore

    df["benchmark_date"] = df.index.map(lambda x: _safe_replace_year(x, benchmark_year))
    benchmark_date_col = df.columns[-1]
    df = df.dropna(subset=[benchmark_date_col])

    seasonal_df = df.pivot_table(index=benchmark_date_col, columns=df.index.year, values=df.columns)  # type: ignore
    seasonal_df = seasonal_df.reindex(benchmark_index)

    return seasonal_df