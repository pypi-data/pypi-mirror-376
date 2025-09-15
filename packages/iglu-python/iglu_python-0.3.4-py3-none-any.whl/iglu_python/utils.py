from datetime import datetime
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from tzlocal import get_localzone

local_tz = get_localzone()  # get the local timezone

_IGLU_R_COMPATIBLE = True


def set_iglu_r_compatible(value: bool) -> None:
    global _IGLU_R_COMPATIBLE
    _IGLU_R_COMPATIBLE = value


def is_iglu_r_compatible() -> bool:
    global _IGLU_R_COMPATIBLE
    return _IGLU_R_COMPATIBLE


def localize_naive_timestamp(timestamp: datetime) -> datetime:
    """
    Localize a naive timestamp to the local timezone.
    """
    if timestamp.tzinfo is None:
        # Handle ambiguous times (e.g., DST transitions) by specifying 'ambiguous' argument
        # Default to 'NaT' for ambiguous times, but you may choose 'raise' or 'infer' as needed
        return timestamp.tz_localize(local_tz, ambiguous="NaT")
    else:
        return timestamp


def localize_naive_timestamp_to_UTC(timestamp: datetime) -> datetime:
    """
    Localize a naive timestamp to the UTC timezone.
    """
    if timestamp.tzinfo is None:
        # Handle ambiguous times (e.g., DST transitions) by specifying 'ambiguous' argument
        # Default to 'NaT' for ambiguous times, but you may choose 'raise' or 'infer' as needed
        return timestamp.tz_localize("UTC")
    else:
        return timestamp


def set_local_tz(tz: str) -> None:
    """
    Set the local timezone.
    It used ONLY in the unittests to fix configuration as in expected results.
    """
    global local_tz
    local_tz = ZoneInfo(tz)


def get_local_tz():
    global local_tz
    return local_tz


def check_data_columns(data: pd.DataFrame, time_check=False, tz="") -> pd.DataFrame:
    """
    Check if the input DataFrame has the required columns and correct data types.

    Parameters
    ----------
    data : pd.DataFrame
        Input DataFrame to check
    tz : str, default=""
        Time zone to use for calculations
        If tz is not "", the time column is converted to the specified timezone
        if tz is "", the time column is converted to UTC timezone

    Returns
    -------
    pd.DataFrame
        Validated DataFrame

    Raises
    ------
    ValueError
        If required columns are missing or data types are incorrect
    """
    required_columns = ["id", "time", "gl"]

    # Check if all required columns exist
    missing_cols = [col for col in required_columns if col not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Create a copy to avoid dtype warning
    data = data.copy()

    # Check data types
    if not pd.api.types.is_numeric_dtype(data["gl"]):
        try:
            data["gl"] = pd.to_numeric(data["gl"])
        except Exception as e:
            raise ValueError("Column 'gl' must be numeric") from e

    if not pd.api.types.is_datetime64_any_dtype(data["time"]):
        try:
            data["time"] = pd.to_datetime(data["time"])
        except Exception as e:
            raise ValueError("Column 'time' must be datetime") from e

    if not pd.api.types.is_string_dtype(data["id"]):
        data["id"] = data["id"].astype(str)

    # check if data frame empty
    if data.empty:
        raise ValueError("Data frame is empty")

    # Check if data contains no glucose values
    if data["gl"].isna().all():
        raise ValueError("Data contains no glucose values")

    # Check for missing values
    # if data["gl"].isna().any():
    #     warnings.warn("Data contains missing glucose values")

    # convert time to specified timezone
    # TODO: check if this is correct (R-implementation compatibility)
    # if tz and tz != "":
    #     # First remove timezone information, then localize to specified timezone
    #     data['time'] = pd.to_datetime(data['time']).dt.tz_localize(None).dt.tz_localize(tz)
    #
    # this is implementation compatible with R implementation
    # but seems incorrect, as it convert time to TZ instead of localizing it to TZ
    if tz != "":
        # Create a copy to avoid dtype warning and properly handle timezone conversion
        data["time"] = pd.to_datetime(data["time"]).apply(localize_naive_timestamp).dt.tz_convert(tz)
    else:
        # Create a copy to avoid dtype warning
        data["time"] = pd.to_datetime(data["time"]).apply(localize_naive_timestamp_to_UTC)

    # Drop rows where 'time' is NaT
    data = data[~pd.isna(data["time"])]

    return data


def CGMS2DayByDay(  # noqa: C901
    data: pd.DataFrame | pd.Series,
    dt0: Optional[pd.Timestamp] = None,
    inter_gap: int = 45,
    tz: str = "",
) -> Tuple[np.ndarray, list, int]:
    """
    Interpolate glucose values onto an equally spaced grid from day to day.

    The function takes CGM data and interpolates it onto a uniform time grid,
    with each row representing a day and each column representing a time point.
    Missing values are linearly interpolated when close enough to non-missing values.

    data : pd.DataFrame or pd.Series
        DataFrame with columns 'id', 'time', and 'gl'. Should only be data for 1 subject.
        In case multiple subject ids are detected, a warning is produced and only 1st subject is used.
    dt0 : int, optional
        The time frequency for interpolation in minutes. If None, will match the CGM meter's frequency
        (e.g., 5 min for Dexcom).
    inter_gap : int, default=45
        The maximum allowable gap (in minutes) for interpolation. Values will not be interpolated
        between glucose measurements that are more than inter_gap minutes apart.
    tz : str, default=""
        Time zone to use for datetime conversion. Empty string means use local time zone.

    Returns
    -------
    Tuple[np.ndarray, list, int, list]
        A tuple containing:
        - gd2d: A 2D numpy array of glucose values with each row corresponding to a new day,
               and each column corresponding to time
        - actual_dates: A list of dates corresponding to the rows of gd2d
        - dt0: Time frequency of the resulting grid, in minutes
    Examples
    --------
    >>> data = pd.DataFrame({
    ...     'id': ['subject1'] * 4,
    ...     'time': pd.to_datetime(['2020-01-01 00:00:00', '2020-01-01 00:05:00',
    ...                            '2020-01-01 00:10:00', '2020-01-01 00:15:00']),
    ...     'gl': [150, 200, 180, 160]
    ... })
    >>> gd2d, dates, dt = CGMS2DayByDay(data)
    >>> print(gd2d.shape)  # Shape will be (1, 288) for one day with 5-min intervals
    (1, 288)
    """
    # Handle Series input
    if isinstance(data, pd.Series):
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError("Series must have a DatetimeIndex")
        data = pd.DataFrame(
            {
                "id": ["subject1"] * len(data.values),
                "time": data.index,
                "gl": data.values,
            }
        )
    # Check data format
    data = check_data_columns(data, tz)

    # Get unique subjects
    subjects = data["id"].unique()
    if len(subjects) > 1:
        raise ValueError("Multiple subjects detected. Please provide a single subject.")

    # Sort by time
    data = data.sort_values("time")

    # Calculate time step (dt0)
    if dt0 is None:
        # Use most common time difference
        time_diffs = data["time"].diff().dropna()
        # Only consider time differences >= 1 minute when computing the mode
        time_diffs_filtered = time_diffs[time_diffs.dt.total_seconds() >= 60]
        if len(time_diffs_filtered) == 0:
            raise ValueError("No time differences >= 1 minute found to compute dt0.")
        dt0 = int(time_diffs_filtered.mode().iloc[0].total_seconds() / 60)

    # Create time grid
    start_time = data["time"].min().floor("D")
    end_time = data["time"].max().ceil("D")
    time_grid = pd.date_range(start=start_time, end=end_time, freq=f"{dt0}min")
    if is_iglu_r_compatible():
        # remove the first time point
        time_grid = time_grid[1:]
    else:
        # remove the last time point
        time_grid = time_grid[:-1]

    # find gaps in the data (using original data indexes, not time grid)
    gaps = []
    for i in range(len(data) - 1):
        if (data["time"].iloc[i + 1] - data["time"].iloc[i]).total_seconds() > inter_gap * 60:
            gaps.append((i, i + 1))

    # Interpolate glucose values
    # Note: doesn't work right with DST crossings
    # During DST spring forward (March 12, 2023)
    # 2:00 AM → 3:00 AM (hour is skipped)
    # Your current code would try to interpolate:
    # 2:30 AM → ??? (this time doesn't exist!)
    # np.interp will linearly interpolate between 2:00 AM and 3:00 AM
    # giving you a glucose value for a non-existent time
    # TODO: fix this
    interp_data = np.interp(
        (time_grid - start_time).total_seconds() / 60,
        (data["time"] - start_time).dt.total_seconds() / 60,
        data["gl"],
        left=np.nan,
        right=np.nan,
    )

    # put nan in the gaps
    for gap in gaps:
        gap_start_idx = gap[0]
        gap_start_time = data["time"].iloc[gap_start_idx]
        # find the index of the gap start in the time grid
        gap_start_idx_in_time_grid = int(np.floor((gap_start_time - start_time).total_seconds() / (60 * dt0)))
        gap_end_idx = gap[1]
        gap_end_time = data["time"].iloc[gap_end_idx]
        # find the index of the gap end in the time grid
        gap_end_idx_in_time_grid = int(
            # -1sec to indicate time before measurement
            np.floor(((gap_end_time - start_time).total_seconds() - 1) / (60 * dt0))
        )
        # put nan in the gap
        interp_data[gap_start_idx_in_time_grid:gap_end_idx_in_time_grid] = np.nan

    # for compatibility with the R package, set values to nan before data['time'].min() and after data['time'].max()
    # find index of timegrid before data['time'].min() and after data['time'].max()
    # head_min_idx = np.where(time_grid >= data['time'].min())[0][0]
    # tail_max_idx = np.where(time_grid <= data['time'].max())[0][-1] + 1
    # interp_data[:head_min_idx] = np.nan
    # interp_data[tail_max_idx:] = np.nan

    # Reshape to days
    n_days = (end_time - start_time).days
    n_points_per_day = 24 * 60 // dt0

    # workaround for misalignment, probably due to DST crossings
    # ToDo: fix it!
    if interp_data.shape[0] != n_days * n_points_per_day:
        # cut or pad interp_data to n_days*n_point_per_day
        target_size = n_days * n_points_per_day
        if interp_data.shape[0] > target_size:
            interp_data = interp_data[:target_size]
        elif interp_data.shape[0] < target_size:
            interp_data = np.pad(interp_data, (0, target_size - interp_data.shape[0]), constant_values=np.nan)
    interp_data = interp_data.reshape(n_days, n_points_per_day)

    # Get actual dates
    if is_iglu_r_compatible():
        # convert start_time into naive datetime
        start_time = start_time.tz_localize(None)

    actual_dates = [start_time + pd.Timedelta(days=i) for i in range(n_days)]

    return interp_data, actual_dates, dt0


def gd2d_to_df(gd2d, actual_dates, dt0):
    """Convert gd2d (CGMS2DayByDay output) to a pandas DataFrame"""
    df = pd.DataFrame({"time": [], "gl": []})

    gl = gd2d.flatten().tolist()
    time = []
    for day in range(gd2d.shape[0]):
        n = len(gd2d[day, :])
        day_time = [pd.Timedelta(i * dt0, unit="m") + actual_dates[day] for i in range(n)]
        time.extend(day_time)

    df = pd.DataFrame({"time": pd.Series(time), "gl": pd.Series(gl, dtype="float64")})

    return df
