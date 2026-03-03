"""
stocks.services — business-logic layer for stock data pipeline.

Public API
----------
fetch_and_store_bhavcopy(date)
calculate_oi_change_for_date(date)
calculate_volume_spike_for_date(date)
generate_signals_for_date(date)
run_daily_pipeline(date)
"""

import logging
from datetime import date

from .bhavcopy_service import fetch_and_store_bhavcopy
from .oi_change_service import calculate_oi_change_for_date
from .volume_spike_service import calculate_volume_spike_for_date
from .signal_service import generate_signals_for_date

logger = logging.getLogger(__name__)

__all__ = [
    'fetch_and_store_bhavcopy',
    'calculate_oi_change_for_date',
    'calculate_volume_spike_for_date',
    'generate_signals_for_date',
    'run_daily_pipeline',
]


def run_daily_pipeline(target_date: date) -> dict:
    """
    Execute the full daily analytics pipeline in the correct order:

        1. fetch_and_store_bhavcopy      (data ingestion)
        2. calculate_oi_change_for_date   (depends on #1)
        3. calculate_volume_spike_for_date(depends on #1, parallel with #2)
        4. calculate_market_bias_for_date (independent)
        5. generate_signals_for_date      (depends on #2, #3, #4)

    Returns a summary dict with counts from each step.
    """
    from global_market.services import (
        fetch_global_market_data,
        calculate_market_bias_for_date,
    )

    logger.info("=== Starting daily pipeline for %s ===", target_date)
    results = {}

    # Step 1: Ingest bhavcopy (may resolve to an earlier trading day)
    bhavcopy_rows, actual_date = fetch_and_store_bhavcopy(target_date)
    results['bhavcopy_rows'] = bhavcopy_rows
    results['actual_date'] = str(actual_date)

    if actual_date != target_date:
        logger.info(
            "Bhavcopy not available for %s (holiday/weekend), "
            "using %s instead. All subsequent steps use %s.",
            target_date, actual_date, actual_date,
        )

    # Use actual trading date for all subsequent steps
    trading_date = actual_date

    # Steps 2 & 3: OI change and volume spike (both depend on #1)
    results['oi_change_updated'] = calculate_oi_change_for_date(trading_date)
    results['volume_spike_updated'] = calculate_volume_spike_for_date(trading_date)

    # Step 4: Fetch global market data (independent of stock data)
    gm = fetch_global_market_data(trading_date)
    results['global_market_fetched'] = gm is not None

    # Step 5: Calculate market bias (depends on #4)
    results['market_bias'] = calculate_market_bias_for_date(trading_date)

    # Step 6: Signal generation (depends on #2, #3, #5)
    results['signals_generated'] = generate_signals_for_date(trading_date)

    logger.info("=== Pipeline complete for %s: %s ===", trading_date, results)
    return results
