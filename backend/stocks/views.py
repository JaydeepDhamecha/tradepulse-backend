from datetime import date

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import IntradaySignal, Stock
from .serializers import IntradaySignalSerializer, StockSerializer


class _DateFilterMixin:
    """Adds ?date=YYYY-MM-DD query-param filtering."""

    def get_target_date(self) -> date | None:
        date_str = self.request.query_params.get('date')
        if date_str:
            try:
                return date.fromisoformat(date_str)
            except ValueError:
                return None
        return None


class TopDeliveryView(_DateFilterMixin, generics.ListAPIView):
    """
    GET /api/stocks/top-delivery/?date=YYYY-MM-DD
    Returns stocks ordered by delivery_percentage (desc).
    Defaults to the most recent date with data.
    """
    serializer_class = StockSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        target = self.get_target_date()
        qs = Stock.objects.filter(delivery_percentage__isnull=False)

        if target:
            qs = qs.filter(date=target)
        else:
            latest_date = qs.order_by('-date').values_list('date', flat=True).first()
            if latest_date:
                qs = qs.filter(date=latest_date)

        return qs.order_by('-delivery_percentage')


class VolumeSpikeView(_DateFilterMixin, generics.ListAPIView):
    """
    GET /api/stocks/volume-spike/?date=YYYY-MM-DD
    Returns stocks ordered by volume_spike_ratio (desc).
    Defaults to the most recent date with data.
    """
    serializer_class = StockSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        target = self.get_target_date()
        qs = Stock.objects.filter(volume_spike_ratio__isnull=False)

        if target:
            qs = qs.filter(date=target)
        else:
            latest_date = qs.order_by('-date').values_list('date', flat=True).first()
            if latest_date:
                qs = qs.filter(date=latest_date)

        return qs.order_by('-volume_spike_ratio')


class IntradaySignalView(_DateFilterMixin, generics.ListAPIView):
    """
    GET /api/stocks/intraday-signals/?date=YYYY-MM-DD&signal_type=BUY
    Returns signals with optional date and signal_type filtering.
    Defaults to the most recent date with data.
    """
    serializer_class = IntradaySignalSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        target = self.get_target_date()
        qs = IntradaySignal.objects.select_related('stock')

        if target:
            qs = qs.filter(date=target)
        else:
            latest_date = qs.order_by('-date').values_list('date', flat=True).first()
            if latest_date:
                qs = qs.filter(date=latest_date)

        signal_type = self.request.query_params.get('signal_type', '').upper()
        if signal_type in ('BUY', 'SELL', 'HOLD'):
            qs = qs.filter(signal_type=signal_type)

        return qs.order_by('-confidence_score')
