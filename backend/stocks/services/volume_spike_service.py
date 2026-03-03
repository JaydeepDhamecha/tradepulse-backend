"""
Compute volume spike ratio for every stock on a given date.

volume_spike_ratio = today_volume / 20-day rolling average volume
"""

import logging
from datetime import date
from decimal import Decimal

import pandas as pd
from django.conf import settings as django_settings

from stocks.models import Stock

logger = logging.getLogger(__name__)


def calculate_volume_spike_for_date(target_date: date) -> int:
    """
    For each Stock row on *target_date*, compute:
        volume_spike_ratio = today_volume / avg(volume over prior N days)

    where N = settings.VOLUME_SPIKE_LOOKBACK_DAYS (default 20).

    Returns the number of rows updated.
    """
    lookback = getattr(django_settings, 'VOLUME_SPIKE_LOOKBACK_DAYS', 20)

    # Get today's stocks
    today_qs = Stock.objects.filter(date=target_date)
    symbols = list(today_qs.values_list('symbol', flat=True))

    if not symbols:
        logger.info("No stocks found on %s — skipping volume spike", target_date)
        return 0

    # Fetch historical volume data for these symbols over the lookback window
    historical_qs = (
        Stock.objects
        .filter(symbol__in=symbols, date__lt=target_date)
        .order_by('symbol', '-date')
        .values('symbol', 'date', 'volume')
    )

    # Convert to DataFrame for efficient rolling computation
    if not historical_qs.exists():
        logger.info("No historical data before %s — skipping volume spike", target_date)
        return 0

    hist_df = pd.DataFrame.from_records(historical_qs)

    # Keep only the most recent `lookback` days per symbol
    hist_df = (
        hist_df
        .sort_values(['symbol', 'date'], ascending=[True, False])
        .groupby('symbol')
        .head(lookback)
    )

    # Compute average volume per symbol
    avg_vol = (
        hist_df
        .groupby('symbol')['volume']
        .mean()
        .to_dict()
    )

    # Update today's stocks
    today_stocks = list(today_qs)
    bulk = []

    for stock in today_stocks:
        avg = avg_vol.get(stock.symbol)
        if avg is None or avg == 0:
            continue

        ratio = Decimal(str(round(stock.volume / avg, 4)))
        stock.volume_spike_ratio = ratio
        bulk.append(stock)

    if bulk:
        Stock.objects.bulk_update(bulk, fields=['volume_spike_ratio'], batch_size=500)

    logger.info("Updated volume spike for %d / %d stocks on %s",
                len(bulk), len(today_stocks), target_date)
    return len(bulk)
