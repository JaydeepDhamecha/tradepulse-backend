"""
global_market.services — business-logic layer for global market data.

Public API
----------
calculate_market_bias_for_date(date)
"""

from .market_bias_service import calculate_market_bias_for_date

__all__ = [
    'calculate_market_bias_for_date',
]
