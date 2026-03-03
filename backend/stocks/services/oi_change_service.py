"""
Compute OI change for every stock on a given date.

oi_change = current open_interest − previous trading day's open_interest
"""

import logging
from datetime import date, timedelta

from django.db.models import F

from stocks.models import Stock

logger = logging.getLogger(__name__)


def _find_previous_trading_date(target_date: date) -> date | None:
    """
    Return the most recent date *before* target_date that has Stock rows,
    or None if no prior data exists.
    """
    prev = (
        Stock.objects
        .filter(date__lt=target_date)
        .order_by('-date')
        .values_list('date', flat=True)
        .first()
    )
    return prev


def calculate_oi_change_for_date(target_date: date) -> int:
    """
    For every Stock row on *target_date* that has an open_interest value,
    compute oi_change = open_interest − previous day's open_interest.

    Also stores previous_open_interest for reference.

    Returns the number of rows updated.
    """
    prev_date = _find_previous_trading_date(target_date)
    if prev_date is None:
        logger.warning("No previous trading day found before %s — skipping OI change", target_date)
        return 0

    # Build a map: symbol → previous OI
    prev_oi_map = dict(
        Stock.objects
        .filter(date=prev_date, open_interest__isnull=False)
        .values_list('symbol', 'open_interest')
    )

    if not prev_oi_map:
        logger.info("No OI data on previous date %s — nothing to compute", prev_date)
        return 0

    # Fetch today's stocks that have OI
    today_stocks = Stock.objects.filter(
        date=target_date,
        open_interest__isnull=False,
    )

    updated = 0
    bulk = []

    for stock in today_stocks.iterator():
        prev_oi = prev_oi_map.get(stock.symbol)
        if prev_oi is None:
            continue

        stock.previous_open_interest = prev_oi
        stock.oi_change = stock.open_interest - prev_oi
        bulk.append(stock)

    if bulk:
        Stock.objects.bulk_update(
            bulk,
            fields=['previous_open_interest', 'oi_change'],
            batch_size=500,
        )
        updated = len(bulk)

    logger.info("Updated OI change for %d stocks on %s (prev date: %s)",
                updated, target_date, prev_date)
    return updated
