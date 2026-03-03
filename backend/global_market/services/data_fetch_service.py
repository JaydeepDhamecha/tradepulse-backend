"""
Fetch global market data from Yahoo Finance and upsert into GlobalMarket model.

Tickers used:
  - GIFT Nifty proxy  → ^NSEI  (Nifty 50 index)
  - Dow Jones         → ^DJI
  - Nasdaq Composite  → ^IXIC

Each value includes LTP (last close) and daily % change.
"""

import logging
from datetime import date
from decimal import Decimal

from django.db import transaction

from global_market.models import GlobalMarket

logger = logging.getLogger(__name__)

# Yahoo Finance ticker mapping
_TICKERS = {
    'gift_nifty': '^NSEI',   # Nifty 50 as GIFT Nifty proxy
    'dow_jones': '^DJI',
    'nasdaq': '^IXIC',
}


def _fetch_yahoo_data(ticker: str, label: str) -> tuple[Decimal | None, Decimal | None]:
    """
    Fetch the latest LTP and daily % change for a Yahoo Finance ticker.
    Returns (ltp, pct_change) — either can be None on failure.
    """
    try:
        import yfinance as yf

        tk = yf.Ticker(ticker)
        hist = tk.history(period='5d')

        if hist.empty or len(hist) < 2:
            logger.warning("Not enough data for %s (%s)", label, ticker)
            return None, None

        prev_close = hist['Close'].iloc[-2]
        last_close = hist['Close'].iloc[-1]

        ltp = Decimal(str(round(float(last_close), 2)))

        if prev_close == 0:
            return ltp, None

        pct_change = ((last_close - prev_close) / prev_close) * 100
        change = Decimal(str(round(pct_change, 4)))

        return ltp, change

    except Exception as exc:
        logger.warning("Failed to fetch %s (%s): %s", label, ticker, exc)
        return None, None


def fetch_global_market_data(target_date: date) -> GlobalMarket:
    """
    Fetch real global market data from Yahoo Finance and upsert
    a GlobalMarket row for *target_date*.

    Fetches LTP and daily % change for:
      - Nifty 50 (proxy for GIFT Nifty)
      - Dow Jones Industrial Average
      - Nasdaq Composite

    Returns the GlobalMarket instance (created or updated).
    """
    logger.info("Fetching global market data from Yahoo Finance for %s...", target_date)

    gift_ltp, gift_change = _fetch_yahoo_data(_TICKERS['gift_nifty'], 'GIFT Nifty')
    dow_ltp, dow_change = _fetch_yahoo_data(_TICKERS['dow_jones'], 'Dow Jones')
    nasdaq_ltp, nasdaq_change = _fetch_yahoo_data(_TICKERS['nasdaq'], 'Nasdaq')

    logger.info(
        "Yahoo Finance data: GIFT Nifty=%s (%.2f%%), Dow=%s (%.2f%%), Nasdaq=%s (%.2f%%)",
        gift_ltp, gift_change or 0, dow_ltp, dow_change or 0, nasdaq_ltp, nasdaq_change or 0,
    )

    # Upsert: one record per date
    with transaction.atomic():
        gm, created = GlobalMarket.objects.update_or_create(
            date=target_date,
            defaults={
                'gift_nifty_ltp': gift_ltp,
                'dow_jones_ltp': dow_ltp,
                'nasdaq_ltp': nasdaq_ltp,
                'gift_nifty_change': gift_change,
                'dow_jones_change': dow_change,
                'nasdaq_change': nasdaq_change,
            },
        )

    action = 'Created' if created else 'Updated'
    logger.info("%s GlobalMarket row for %s (id=%d)", action, target_date, gm.pk)
    return gm
