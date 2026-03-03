"""
Multi-factor signal scoring → IntradaySignal (BUY / SELL / HOLD).

Five factors are combined into a weighted composite score (0–100):
    price_change    (0.25)  – % change in close price
    volume_spike    (0.25)  – today_vol / 20-day avg
    oi_change       (0.20)  – change in open interest
    delivery_pct    (0.15)  – delivery percentage
    market_bias     (0.15)  – global market sentiment score

Each factor is linearly interpolated to a 0–100 scale using configurable
min/max ranges.  The composite score determines the signal:
    >= 60 → BUY
    <= 40 → SELL
    else  → HOLD
"""

import logging
from datetime import date
from decimal import Decimal

from django.conf import settings as django_settings
from django.db import transaction

from global_market.models import GlobalMarket
from stocks.models import IntradaySignal, Stock

logger = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────────

def _lerp(value: float, lo: float, hi: float) -> float:
    """Linearly interpolate *value* from [lo, hi] → [0, 100], clamped."""
    if hi == lo:
        return 50.0
    normalized = (value - lo) / (hi - lo) * 100.0
    return max(0.0, min(100.0, normalized))


def _market_bias_score(bias: str) -> float:
    """Map bias label to a numeric 0-100 score."""
    return {
        'BULLISH': 80.0,
        'NEUTRAL': 50.0,
        'BEARISH': 20.0,
    }.get(bias, 50.0)


# ── main entry point ─────────────────────────────────────────────

def generate_signals_for_date(target_date: date) -> int:
    """
    Score every Stock row on *target_date* and create/update IntradaySignal rows.

    Returns the number of signals generated.
    """
    weights = django_settings.SIGNAL_WEIGHTS
    ranges = django_settings.SIGNAL_FACTOR_RANGES
    buy_threshold = django_settings.SIGNAL_BUY_THRESHOLD
    sell_threshold = django_settings.SIGNAL_SELL_THRESHOLD

    # Fetch market bias for the date
    try:
        gm = GlobalMarket.objects.get(date=target_date)
        bias = gm.market_bias
    except GlobalMarket.DoesNotExist:
        bias = 'NEUTRAL'

    bias_score = _market_bias_score(bias)

    stocks = Stock.objects.filter(date=target_date)

    if not stocks.exists():
        logger.info("No stocks on %s — skipping signal generation", target_date)
        return 0

    signals_to_create = []
    signals_to_update = []

    # Pre-fetch existing signals for this date to decide create vs update
    existing_signals = {
        (sig.stock_id, sig.signal_type): sig
        for sig in IntradaySignal.objects.filter(date=target_date)
    }

    for stock in stocks.iterator():
        # --- Compute individual factor scores ---
        factor_scores = {}

        # 1. Price change
        if stock.price_change_percent is not None:
            lo, hi = ranges['price_change']
            factor_scores['price_change'] = _lerp(float(stock.price_change_percent), lo, hi)
        else:
            factor_scores['price_change'] = 50.0  # neutral default

        # 2. Volume spike
        if stock.volume_spike_ratio is not None:
            lo, hi = ranges['volume_spike']
            factor_scores['volume_spike'] = _lerp(float(stock.volume_spike_ratio), lo, hi)
        else:
            factor_scores['volume_spike'] = 50.0

        # 3. OI change
        if stock.oi_change is not None:
            lo, hi = ranges['oi_change']
            factor_scores['oi_change'] = _lerp(float(stock.oi_change), lo, hi)
        else:
            factor_scores['oi_change'] = 50.0

        # 4. Delivery percentage
        if stock.delivery_percentage is not None:
            lo, hi = ranges['delivery_pct']
            factor_scores['delivery_pct'] = _lerp(float(stock.delivery_percentage), lo, hi)
        else:
            factor_scores['delivery_pct'] = 50.0

        # 5. Market bias (same for all stocks on this date)
        factor_scores['market_bias'] = bias_score

        # --- Weighted composite ---
        composite = sum(
            factor_scores[factor] * weight
            for factor, weight in weights.items()
        )
        composite = round(composite, 2)

        # --- Determine signal type ---
        if composite >= buy_threshold:
            signal_type = IntradaySignal.SignalType.BUY
        elif composite <= sell_threshold:
            signal_type = IntradaySignal.SignalType.SELL
        else:
            signal_type = IntradaySignal.SignalType.HOLD

        # --- Build reasoning ---
        reasoning = (
            f"Composite={composite:.1f} | "
            f"price_change={factor_scores['price_change']:.1f} "
            f"vol_spike={factor_scores['volume_spike']:.1f} "
            f"oi={factor_scores['oi_change']:.1f} "
            f"delivery={factor_scores['delivery_pct']:.1f} "
            f"bias={factor_scores['market_bias']:.1f}"
        )

        key = (stock.id, signal_type)
        if key in existing_signals:
            sig = existing_signals[key]
            sig.confidence_score = Decimal(str(composite))
            sig.reasoning_summary = reasoning
            signals_to_update.append(sig)
        else:
            signals_to_create.append(
                IntradaySignal(
                    stock=stock,
                    date=target_date,
                    signal_type=signal_type,
                    confidence_score=Decimal(str(composite)),
                    reasoning_summary=reasoning,
                )
            )

    with transaction.atomic():
        if signals_to_create:
            IntradaySignal.objects.bulk_create(signals_to_create, batch_size=500)
        if signals_to_update:
            IntradaySignal.objects.bulk_update(
                signals_to_update,
                fields=['confidence_score', 'reasoning_summary'],
                batch_size=500,
            )

    total = len(signals_to_create) + len(signals_to_update)
    logger.info(
        "Generated %d signals for %s (created=%d, updated=%d)",
        total, target_date, len(signals_to_create), len(signals_to_update),
    )
    return total
