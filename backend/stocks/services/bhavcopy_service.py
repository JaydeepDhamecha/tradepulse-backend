"""
Fetch NSE bhavcopy CSV for a given date, parse it, and bulk-upsert Stock rows.
"""

import io
import logging
import zipfile
from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import requests
from django.conf import settings
from django.db import transaction

from stocks.models import Stock

logger = logging.getLogger(__name__)

# ── NSE headers (required to bypass 403) ────────────────────────
_NSE_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/',
}

# Column mapping: bhavcopy CSV column → Stock model field
_COL_MAP = {
    'SYMBOL': 'symbol',
    'OPEN': 'open',
    'HIGH': 'high',
    'LOW': 'low',
    'CLOSE': 'close',
    'TOTTRDQTY': 'volume',
    'DELIV_PER': 'delivery_percentage',
}


def _build_url(target_date: date) -> str:
    """Return the bhavcopy ZIP URL for *target_date*."""
    return settings.NSE_BHAVCOPY_URL.format(
        year=target_date.strftime('%Y'),
        month=target_date.strftime('%b').upper(),
        date=target_date.strftime('%d%b%Y').upper(),
    )


def _get_session() -> requests.Session:
    """Return a requests.Session pre-loaded with NSE cookies."""
    session = requests.Session()
    session.headers.update(_NSE_HEADERS)
    # Hit main page first to obtain cookies
    session.get(settings.NSE_BASE_URL, timeout=10)
    return session


def _download_csv(session: requests.Session, url: str) -> pd.DataFrame:
    """Download the ZIP, extract the CSV, return a DataFrame."""
    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_name = zf.namelist()[0]
        with zf.open(csv_name) as csv_file:
            df = pd.read_csv(csv_file)

    # Normalise column names (strip whitespace)
    df.columns = df.columns.str.strip()
    return df


def _safe_decimal(value, default=None) -> Decimal | None:
    """Convert a value to Decimal, returning *default* on failure."""
    if pd.isna(value):
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return default


def _safe_int(value, default=None) -> int | None:
    """Convert a value to int, returning *default* on failure."""
    if pd.isna(value):
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def fetch_and_store_bhavcopy(target_date: date) -> int:
    """
    Download the NSE bhavcopy for *target_date*, filter equity rows,
    and bulk-upsert into the Stock table.

    Returns the number of rows upserted.
    """
    url = _build_url(target_date)
    logger.info("Fetching bhavcopy from %s", url)

    session = _get_session()
    df = _download_csv(session, url)

    # Keep only equity series
    if 'SERIES' in df.columns:
        df = df[df['SERIES'].str.strip() == 'EQ']

    logger.info("Parsed %d EQ rows for %s", len(df), target_date)

    # Compute price_change_percent from CLOSE & PREVCLOSE if available
    if {'CLOSE', 'PREVCLOSE'}.issubset(df.columns):
        df['_price_change_pct'] = (
            (df['CLOSE'] - df['PREVCLOSE']) / df['PREVCLOSE'] * 100
        )
    else:
        df['_price_change_pct'] = None

    # Look up existing symbols for this date to decide create vs update
    existing = set(
        Stock.objects.filter(date=target_date).values_list('symbol', flat=True)
    )

    to_create = []
    to_update = []

    for _, row in df.iterrows():
        symbol = str(row.get('SYMBOL', '')).strip()
        if not symbol:
            continue

        fields = {
            'symbol': symbol,
            'date': target_date,
            'open': _safe_decimal(row.get('OPEN'), Decimal('0')),
            'high': _safe_decimal(row.get('HIGH'), Decimal('0')),
            'low': _safe_decimal(row.get('LOW'), Decimal('0')),
            'close': _safe_decimal(row.get('CLOSE'), Decimal('0')),
            'volume': _safe_int(row.get('TOTTRDQTY'), 0),
            'delivery_percentage': _safe_decimal(row.get('DELIV_PER')),
            'price_change_percent': _safe_decimal(row.get('_price_change_pct')),
        }

        if symbol in existing:
            to_update.append(fields)
        else:
            to_create.append(Stock(**fields))

    with transaction.atomic():
        if to_create:
            Stock.objects.bulk_create(to_create, batch_size=500)

        for fields in to_update:
            Stock.objects.filter(
                symbol=fields.pop('symbol'),
                date=fields.pop('date'),
            ).update(**fields)

    total = len(to_create) + len(to_update)
    logger.info("Upserted %d stocks for %s (created=%d, updated=%d)",
                total, target_date, len(to_create), len(to_update))
    return total
