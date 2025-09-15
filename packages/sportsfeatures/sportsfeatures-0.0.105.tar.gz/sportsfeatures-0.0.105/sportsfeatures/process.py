"""The main process function."""

# pylint: disable=too-many-arguments,too-many-positional-arguments
import datetime

import pandas as pd
import requests_cache
import tqdm

from .bets_process import bet_process
from .datetime_process import datetime_process
from .datetimesub_process import datetimesub_process
from .distance_process import distance_process
from .identifier import Identifier
from .image_process import image_process
from .lastplayed_process import lastplayed_process
from .margin_process import margin_process
from .news_process import news_process
from .offensive_efficiency_process import offensive_efficiency_process
from .ordinal_process import ordinal_process
from .players_process import players_process
from .remove_process import remove_process
from .skill_process import skill_process
from .timeseries_process import timeseries_process
from .win_process import win_process


def _reduce_memory_usage(df: pd.DataFrame) -> pd.DataFrame:
    for col in tqdm.tqdm(df.columns, desc="Downcasting Columns"):
        if df[col].dtype == "int64":
            df[col] = pd.to_numeric(df[col], downcast="integer")
        elif df[col].dtype == "float64":
            df[col] = pd.to_numeric(df[col], downcast="float")
    return df


def process(
    df: pd.DataFrame,
    dt_column: str,
    identifiers: list[Identifier],
    windows: list[datetime.timedelta | None],
    categorical_features: set[str],
    use_bets_features: bool = True,
    use_news_features: bool = True,
    datetime_columns: set[str] | None = None,
    use_players_feature: bool = False,
    session: requests_cache.CachedSession | None = None,
) -> pd.DataFrame:
    """Process the dataframe for sports features."""
    if session is None:
        session = requests_cache.CachedSession(
            "imagefeatures",
            expire_after=requests_cache.NEVER_EXPIRE,
            allowable_methods=("GET", "HEAD", "POST"),
            stale_if_error=True,
        )
    df = skill_process(df, dt_column, identifiers, windows)
    df = offensive_efficiency_process(df, identifiers)
    df = margin_process(df, identifiers)
    df = bet_process(df, identifiers, dt_column, use_bets_features)
    df = datetimesub_process(df, dt_column, identifiers, datetime_columns)
    df = win_process(df, identifiers)
    df = timeseries_process(df, identifiers, windows, dt_column)
    df = datetime_process(df, dt_column, datetime_columns)
    df = distance_process(df, identifiers)
    df = lastplayed_process(df, identifiers, dt_column)
    if use_news_features:
        df = news_process(df, identifiers)
    df = image_process(df, identifiers, session)
    df = ordinal_process(df, categorical_features)
    df = remove_process(df, identifiers)
    if use_players_feature:
        df = players_process(df, identifiers)
    return _reduce_memory_usage(df)
