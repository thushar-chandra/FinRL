"""Minimal adapter: FinRL data pipeline → CA-MARL agent inputs.

Reuses existing FinRL components (FeatureEngineer) without rewriting or
duplicating preprocessing logic. Uses a direct yfinance download in the
adapter because the FinRL YahooDownloader has a yfinance API compatibility
issue (``proxy`` parameter removed in yfinance ≥1.5).

Reference: docs/architecture/ARCHITECTURE.md §1,
docs/architecture/INTERFACE_CONTRACTS.md,
docs/implementation/FINRL_MAPPING.md.
"""

import logging
from typing import Any

import pandas as pd
import yfinance as yf

from finrl.config import INDICATORS
from finrl.meta.preprocessor.preprocessors import FeatureEngineer

logger = logging.getLogger(__name__)


def _download_yahoo(
    ticker_list: list[str],
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Download OHLCV from Yahoo Finance.

    Returns a DataFrame with columns ``[date, open, high, low, close,
    volume, tic]`` — the same schema that ``YahooDownloader`` and
    ``FeatureEngineer`` expect.
    """
    rows: list[pd.DataFrame] = []
    for tic in ticker_list:
        df = yf.download(tic, start=start_date, end=end_date, auto_adjust=True)
        if df.empty:
            continue
        if df.columns.nlevels != 1:
            df.columns = df.columns.droplevel(1)
        df = df.reset_index()
        df["tic"] = tic
        rows.append(df[["Date", "Open", "High", "Low", "Close", "Volume", "tic"]])
    if not rows:
        raise ValueError("No data returned from Yahoo Finance.")
    result = pd.concat(rows, ignore_index=True)
    result.rename(
        columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        },
        inplace=True,
    )
    return result


def download_and_prepare(
    ticker_list: list[str],
    start_date: str,
    end_date: str,
    tech_indicator_list: list[str] | None = None,
) -> dict[str, Any]:
    """Download market data and prepare CA-MARL inputs.

    Steps:
      1. Download OHLCV from Yahoo Finance.
      2. Add technical indicators via ``FeatureEngineer``.
      3. Pivot into ``features`` (T × (n_assets × n_indicators)) and
         ``forward_returns`` (T × n_assets) DataFrames.
      4. Extract close-price matrix for ``realized_prices``.

    Returns a dict with keys ``"features"``, ``"forward_returns"``,
    ``"realized_prices"``, and ``"universe"``, which can be passed directly
    to ``run_pipeline`` (or ``build_agents`` / ``run_inference``).
    """
    if tech_indicator_list is None:
        tech_indicator_list = list(INDICATORS)

    logger.info(
        "Downloading data for %d tickers: %s to %s",
        len(ticker_list), start_date, end_date,
    )
    raw = _download_yahoo(ticker_list, start_date, end_date)

    logger.info("Engineering features with %d indicators...", len(tech_indicator_list))
    fe = FeatureEngineer(
        use_technical_indicator=True,
        tech_indicator_list=tech_indicator_list,
        use_vix=False,
        use_turbulence=False,
    )
    processed = fe.preprocess_data(raw)
    processed = processed.sort_values(["date", "tic"]).reset_index(drop=True)

    # Determine the actual universe (tickers that survived cleaning).
    universe = sorted(processed["tic"].unique().tolist())
    logger.info("Universe: %d tickers", len(universe))

    # Build close-price DataFrame (DatetimeIndex × ticker).
    pivot_close = processed.pivot_table(
        index="date", columns="tic", values="close", aggfunc="first",
    )
    pivot_close.index = pd.to_datetime(pivot_close.index)
    pivot_close = pivot_close[sorted(pivot_close.columns)]

    # Build forward returns: (T × n_assets) one-step fractional returns.
    forward_rets = pivot_close.pct_change().shift(-1).dropna(how="all")
    forward_rets = forward_rets.reindex(sorted(forward_rets.columns), axis=1)

    # Build feature matrix: one row per date, all indicator columns flattened.
    indicator_cols = [c for c in processed.columns if c in tech_indicator_list]
    date_tic_feat = processed.pivot_table(
        index="date", columns="tic", values=indicator_cols, aggfunc="first",
    )
    date_tic_feat.columns = [
        f"{ticker}_{indicator}"
        for indicator, ticker in date_tic_feat.columns
    ]
    date_tic_feat.index = pd.to_datetime(date_tic_feat.index)
    date_tic_feat = date_tic_feat.ffill().bfill().dropna(how="any")

    # Align all three DataFrames to the same date index.
    common_idx = (
        date_tic_feat.index
        .intersection(forward_rets.index)
        .intersection(pivot_close.index)
    )
    features = date_tic_feat.loc[common_idx].reset_index(drop=True)
    forward_returns = forward_rets.loc[common_idx].reset_index(drop=True)
    realized_prices = pivot_close.loc[common_idx]

    logger.info(
        "Prepared: features %s, forward_returns %s, prices %s",
        features.shape, forward_returns.shape, realized_prices.shape,
    )
    return {
        "features": features,
        "forward_returns": forward_returns,
        "universe": universe,
        "realized_prices": realized_prices,
    }
