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
    from global_market.services import calculate_market_bias_for_date

    logger.info("=== Starting daily pipeline for %s ===", target_date)
    results = {}

    # Step 1: Ingest bhavcopy
    results['bhavcopy_rows'] = fetch_and_store_bhavcopy(target_date)

    # Steps 2 & 3: OI change and volume spike (both depend on #1)
    results['oi_change_updated'] = calculate_oi_change_for_date(target_date)
    results['volume_spike_updated'] = calculate_volume_spike_for_date(target_date)

    # Step 4: Market bias (independent of stock data)
    results['market_bias'] = calculate_market_bias_for_date(target_date)

    # Step 5: Signal generation (depends on all above)
    results['signals_generated'] = generate_signals_for_date(target_date)

    logger.info("=== Pipeline complete for %s: %s ===", target_date, results)
    return results
