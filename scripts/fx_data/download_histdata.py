"""Download 1-minute FX bar data from HistData.com via the `histdata` package.

This follows the same approach as the FX-1-Minute-Data project
(https://github.com/philipperemy/FX-1-Minute-Data): HistData.com does not
expose an official API, so the `histdata` pip package reproduces the site's
own download form post to fetch a per-pair, per-period ZIP containing a
semicolon-separated ASCII CSV (no header):

    YYYYMMDD HHMMSS;OPEN;HIGH;LOW;CLOSE;VOLUME   (EST, no DST adjustment)

HistData.com only allows querying a full past YEAR at once, or a single
MONTH for the current year. This module hides that distinction behind a
single date-range API and caches downloaded ZIPs on disk so repeated runs
don't re-download unchanged periods.
"""
import datetime
import io
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
from histdata import download_hist_data
from histdata.api import Platform, TimeFrame

COLUMNS = ["datetime", "open", "high", "low", "close", "volume"]


class PairUnavailableError(Exception):
    """Raised when HistData.com has no data for the requested pair/period."""


@dataclass(frozen=True)
class YearMonth:
    year: int
    month: Optional[int]  # None means "whole year"


def _required_chunks(start_date: datetime.date, end_date: datetime.date, today: Optional[datetime.date] = None):
    """Split [start_date, end_date] into the (year, month) chunks HistData.com expects.

    Past years must be requested whole (month=None); the current year must be
    requested one month at a time (HistData.com/`histdata` rejects the opposite
    combination in either case).
    """
    today = today or datetime.date.today()
    months_touched = set()
    cursor = datetime.date(start_date.year, start_date.month, 1)
    end_marker = datetime.date(end_date.year, end_date.month, 1)
    while cursor <= end_marker:
        months_touched.add((cursor.year, cursor.month))
        if cursor.month == 12:
            cursor = datetime.date(cursor.year + 1, 1, 1)
        else:
            cursor = datetime.date(cursor.year, cursor.month + 1, 1)

    past_years = sorted({y for (y, m) in months_touched if y < today.year})
    current_year_months = sorted(m for (y, m) in months_touched if y == today.year)

    chunks = [YearMonth(year=y, month=None) for y in past_years]
    chunks += [YearMonth(year=today.year, month=m) for m in current_year_months]
    return chunks


def _extract_csv(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise PairUnavailableError(f"No CSV found inside {zip_path}")
        with zf.open(csv_names[0]) as f:
            raw = f.read()
    return pd.read_csv(
        io.BytesIO(raw),
        sep=";",
        header=None,
        names=COLUMNS,
        dtype={"datetime": str},
    )


def fetch_pair_1min(
    pair: str,
    start_date: datetime.date,
    end_date: datetime.date,
    cache_dir: Path,
    verbose: bool = True,
) -> pd.DataFrame:
    """Fetch 1-minute close prices for `pair` (e.g. 'eurjpy') over [start_date, end_date].

    Returns a DataFrame indexed by datetime with a single 'close' column,
    sorted, de-duplicated, and trimmed to the requested range.
    Raises PairUnavailableError if HistData.com has no data for this pair.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    chunks = _required_chunks(start_date, end_date)
    frames = []
    for chunk in chunks:
        month_str = str(chunk.month) if chunk.month is not None else None
        cache_name = "DAT_ASCII_{}_M1_{}.zip".format(
            pair.upper(),
            f"{chunk.year}{chunk.month:02d}" if chunk.month else str(chunk.year),
        )
        cache_path = cache_dir / cache_name
        if not cache_path.exists():
            try:
                downloaded_path = download_hist_data(
                    year=str(chunk.year),
                    month=month_str,
                    pair=pair.lower(),
                    time_frame=TimeFrame.ONE_MINUTE,
                    platform=Platform.GENERIC_ASCII,
                    output_directory=str(cache_dir),
                    verbose=verbose,
                )
                downloaded_path = Path(downloaded_path)
                if downloaded_path != cache_path:
                    downloaded_path.replace(cache_path)
            except AssertionError as e:
                raise PairUnavailableError(f"{pair}: {e}") from e
            except Exception as e:  # network errors, HTML changes, etc.
                raise PairUnavailableError(f"{pair}: {e}") from e
        try:
            frames.append(_extract_csv(cache_path))
        except zipfile.BadZipFile as e:
            cache_path.unlink(missing_ok=True)
            raise PairUnavailableError(f"{pair}: downloaded file was not a valid ZIP ({e})") from e

    if not frames:
        raise PairUnavailableError(f"{pair}: no data chunks resolved for the requested range")

    df = pd.concat(frames, ignore_index=True)
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S")
    df = df.drop_duplicates(subset="datetime").sort_values("datetime")
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1)
    df = df[(df["datetime"] >= start_ts) & (df["datetime"] < end_ts)]
    return df.set_index("datetime")[["close"]]
