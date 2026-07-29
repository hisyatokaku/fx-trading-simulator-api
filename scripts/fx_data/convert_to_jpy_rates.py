"""Convert per-pair 1-minute HistData.com bars into a single JPY-cross-rate CSV.

Output columns/format match sample/rates_1min_sample.csv (DateTime + one column
per currency, each value being "how many JPY per 1 unit of that currency"),
extended to cover every currency in src/main/resources/data/rates.csv.

Currencies HistData.com doesn't carry (either directly as "{CUR}JPY" or via a
"USD{CUR}" pivot) are forward-filled from that existing daily rates.csv instead
of being left blank, since the trading simulator API requires every currency
to have a rate at every tick timestamp.
"""
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from download_histdata import PairUnavailableError, fetch_pair_1min

logger = logging.getLogger(__name__)

# Column order mirrors src/main/resources/data/rates.csv, with TRY appended
# since sample/rates_*_sample.csv already carries it but rates.csv does not.
RATES_CSV_CURRENCIES = [
    "USD", "GBP", "EUR", "CAD", "CHF", "SEK", "DKK", "NOK", "AUD", "NZD",
    "ZAR", "BHD", "HKD", "INR", "PHP", "SGD", "THB", "KWD", "SAR", "AED",
    "MXN", "IDR", "TWD",
]
OUTPUT_CURRENCIES = RATES_CSV_CURRENCIES + ["TRY"]


def load_daily_fallback_rates(rates_csv_path: Path) -> pd.DataFrame:
    """Load the existing daily rates.csv as a date-indexed DataFrame."""
    df = pd.read_csv(rates_csv_path)
    df["Date"] = pd.to_datetime(df["Date"], format="%Y/%m/%d").dt.date
    return df.set_index("Date")


def _fetch_close(pair: str, start_date, end_date, cache_dir: Path) -> Optional[pd.Series]:
    try:
        return fetch_pair_1min(pair, start_date, end_date, cache_dir)["close"]
    except PairUnavailableError as e:
        logger.info("Pair unavailable: %s", e)
        return None


def build_rates(
    start_date: datetime.date,
    end_date: datetime.date,
    cache_dir: Path,
    rates_csv_path: Path,
    currencies: List[str] = OUTPUT_CURRENCIES,
) -> pd.DataFrame:
    direct_series: Dict[str, pd.Series] = {}
    pivot_series: Dict[str, pd.Series] = {}
    fallback_currencies: List[str] = []

    usdjpy = _fetch_close("usdjpy", start_date, end_date, cache_dir)
    if usdjpy is None:
        raise RuntimeError(
            "USDJPY itself is unavailable from HistData.com for this range; "
            "it is the pivot for every other currency, so nothing can proceed."
        )
    direct_series["USD"] = usdjpy

    for currency in currencies:
        if currency == "USD":
            continue
        direct = _fetch_close(f"{currency.lower()}jpy", start_date, end_date, cache_dir)
        if direct is not None:
            direct_series[currency] = direct
            continue
        pivot = _fetch_close(f"usd{currency.lower()}", start_date, end_date, cache_dir)
        if pivot is not None:
            pivot_series[currency] = pivot
            continue
        fallback_currencies.append(currency)

    logger.info("Direct JPY-cross pairs: %s", sorted(direct_series))
    logger.info("Pivoted via USD: %s", sorted(pivot_series))
    if fallback_currencies:
        logger.warning(
            "No HistData.com pair found for %s; falling back to daily rates.csv values.",
            sorted(fallback_currencies),
        )

    combined = pd.concat(direct_series, axis=1) if direct_series else pd.DataFrame()
    combined = combined.sort_index().ffill()

    if pivot_series:
        pivot_df = pd.concat({**pivot_series, "USD": usdjpy}, axis=1).sort_index().ffill()
        for currency in pivot_series:
            combined[currency] = pivot_df["USD"] / pivot_df[currency]

    if fallback_currencies:
        daily = load_daily_fallback_rates(rates_csv_path)
        dates = pd.Series(combined.index.date, index=combined.index)
        for currency in fallback_currencies:
            if currency not in daily.columns:
                logger.warning(
                    "%s is not in %s either; column will be left empty.",
                    currency, rates_csv_path,
                )
                combined[currency] = float("nan")
                continue
            daily_series = daily[currency].sort_index().ffill()
            combined[currency] = dates.map(daily_series)

    combined = combined[currencies]
    still_missing = combined.columns[combined.isna().all()].tolist()
    if still_missing:
        logger.warning("These currencies have no data at all for this range: %s", still_missing)
    return combined


def write_sample_format_csv(df: pd.DataFrame, out_path: Path) -> None:
    lines = ["DateTime," + ",".join(df.columns)]
    for ts, row in df.iterrows():
        dt_str = f"{ts.year}/{ts.month}/{ts.day} {ts.hour}:{ts.minute:02d}"
        values = ",".join("" if pd.isna(v) else f"{v:.4f}" for v in row)
        lines.append(f"{dt_str},{values}")
    out_path.write_text("\n".join(lines) + "\n")
