"""
Compute market bias from global indicators (GIFT Nifty, Dow Jones, Nasdaq).

Weighted score = gift_nifty×0.5 + dow×0.3 + nasdaq×0.2
Score > 0.25  → BULLISH
Score < -0.25 → BEARISH
Otherwise     → NEUTRAL

When an indicator is None, its weight is redistributed proportionally
among the remaining indicators.
"""

import logging
from datetime import date
from decimal import Decimal

from django.conf import settings as django_settings

from global_market.models import GlobalMarket

logger = logging.getLogger(__name__)


def _compute_weighted_score(
    gift_nifty: Decimal | None,
    dow: Decimal | None,
    nasdaq: Decimal | None,
) -> float:
    """Return the weighted composite score, redistributing weights for Nones."""
    weights = django_settings.MARKET_BIAS_WEIGHTS

    components = [
        (float(gift_nifty) if gift_nifty is not None else None, weights['gift_nifty']),
        (float(dow) if dow is not None else None, weights['dow_jones']),
        (float(nasdaq) if nasdaq is not None else None, weights['nasdaq']),
    ]

    # Filter out None values and redistribute weights
    available = [(val, w) for val, w in components if val is not None]

    if not available:
        return 0.0

    total_weight = sum(w for _, w in available)
    score = sum(val * (w / total_weight) for val, w in available)
    return score


def calculate_market_bias_for_date(target_date: date) -> str | None:
    """
    Look up or create the GlobalMarket row for *target_date*,
    compute the weighted bias score, and store the market_bias label.

    Returns the bias string ('BULLISH', 'BEARISH', or 'NEUTRAL'),
    or None if no GlobalMarket row exists for this date.
    """
    try:
        gm = GlobalMarket.objects.get(date=target_date)
    except GlobalMarket.DoesNotExist:
        logger.warning("No GlobalMarket row for %s — cannot compute bias", target_date)
        return None

    score = _compute_weighted_score(
        gm.gift_nifty_change,
        gm.dow_jones_change,
        gm.nasdaq_change,
    )

    bullish_threshold = getattr(django_settings, 'MARKET_BIAS_BULLISH_THRESHOLD', 0.25)
    bearish_threshold = getattr(django_settings, 'MARKET_BIAS_BEARISH_THRESHOLD', -0.25)

    if score > bullish_threshold:
        bias = GlobalMarket.MarketBias.BULLISH
    elif score < bearish_threshold:
        bias = GlobalMarket.MarketBias.BEARISH
    else:
        bias = GlobalMarket.MarketBias.NEUTRAL

    gm.market_bias = bias
    gm.save(update_fields=['market_bias'])

    logger.info("Market bias for %s: %s (score=%.4f)", target_date, bias, score)
    return bias
